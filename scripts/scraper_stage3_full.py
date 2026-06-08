#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第3段（改良版）：XserverのPDFから個別意見＋裁判官名簿を抽出する。
追加点:
  - 末尾の裁判官名簿（裁判長＋裁判官全員）を抽出（panel）。文字間スペースに対応。
  - 異体字の吸収（渡邉=渡辺 など）で judges 照合の精度を上げる。
  - 現職裁判官が関与しているか（hasActiveJudge）を判定 → 第4段のモデル振り分けに使う。
入力 : public/data/opinions_list_stage1.json, public/data/judges.json
出力 : public/data/opinions_detail.json
分割実行: 既処理スキップ、1回 BATCH 件。環境変数: PDF_BASE / BATCH / SLEEP
実行前: pip install requests pdfminer.six
"""
import re, os, sys, json, io, time
import requests
from pdfminer.high_level import extract_text

PDF_BASE = os.environ.get("PDF_BASE", "https://cup1980.xsrv.jp/pdf/")
BATCH = int(os.environ.get("BATCH", "2000"))
SLEEP = float(os.environ.get("SLEEP", "0.1"))
HEADERS = {"User-Agent": "Mozilla/5.0 (SupremeCourtWatch; +github-actions)"}

LIST_JSON = "public/data/opinions_list_stage1.json"
JUDGES_JSON = "public/data/judges.json"
OUT_JSON = "public/data/opinions_detail.json"

HEADING_RE = re.compile(
    r"裁判官([^\sの、。]+?)の(追加反対意見|追加補足意見|反対意見|補足意見|意見)は、次のとおりである。")
SUMMARY_MENTION_RE = re.compile(
    r"裁判官([^\sの、。]+?)の(追加反対意見|追加補足意見|反対意見|補足意見|意見)が(?:ある|あった)")
UNANIMOUS_RE = re.compile(r"裁判官全員一致の意見")
PANEL_RE = re.compile(r"[（(]\s*裁\s*判\s*長\s*裁\s*判\s*官(.+?)[）)]", re.S)

ITAIJI = str.maketrans({"邉":"辺","邊":"辺","惠":"恵","眞":"真","槇":"槙"})

def normalize(text):
    return re.sub(r"-\s*\d+\s*-", "", text)

def norm_name(name):
    n = (name or "").replace(" ", "").replace("　", "")
    return n.translate(ITAIJI)

def extract_opinions(text):
    text = normalize(text)
    summary_mentions = [{"judge": m.group(1), "type": m.group(2)}
                        for m in SUMMARY_MENTION_RE.finditer(text)]
    unanimous = bool(UNANIMOUS_RE.search(text))
    headings = [(m.start(), m.group(1), m.group(2)) for m in HEADING_RE.finditer(text)]
    panel_m = PANEL_RE.search(text)
    panel_pos = panel_m.start() if panel_m else len(text)
    opinions = []
    for i, (pos, judge, otype) in enumerate(headings):
        end = headings[i + 1][0] if i + 1 < len(headings) else (panel_pos if panel_pos > pos else len(text))
        body = text[pos:end].strip()
        opinions.append({"judge": judge, "opinionType": otype, "bodyLength": len(body)})
    set_summary = {(d["judge"], d["type"]) for d in summary_mentions}
    set_body = {(o["judge"], o["opinionType"]) for o in opinions}
    needs_review = (set_summary != set_body)
    return {"unanimous": unanimous, "individualOpinions": opinions, "needsReview": needs_review}

def extract_panel(text):
    text = normalize(text)
    m = PANEL_RE.search(text)
    if not m:
        return []
    block = re.sub(r"\s+", "", m.group(1))
    parts = re.split(r"裁判官", block)
    panel = []
    for i, p in enumerate(parts):
        name = p.strip()
        if name:
            panel.append({"name": name, "presiding": (i == 0)})
    return panel

def load_judges():
    if not os.path.exists(JUDGES_JSON):
        return {}, set()
    judges = json.load(open(JUDGES_JSON, encoding="utf-8"))
    jmap = {norm_name(j["name"]): j["judgeId"] for j in judges}
    active = {j["judgeId"] for j in judges if j.get("status") == "現職"}
    return jmap, active

def link_ids(items, jmap):
    for o in items:
        o["judgeId"] = jmap.get(norm_name(o.get("judge") or o.get("name")))
    return items

def main():
    src = json.load(open(LIST_JSON, encoding="utf-8"))
    jmap, active_ids = load_judges()
    done = {}
    if os.path.exists(OUT_JSON):
        for rec in json.load(open(OUT_JSON, encoding="utf-8")):
            done[rec["hanreiId"]] = rec
    todo = [r for r in src if r["hanreiId"] not in done]
    print(f"全{len(src)}件 / 済{len(done)}件 / 残{len(todo)}件 / 今回最大{BATCH}件", file=sys.stderr)
    processed = 0
    for rec in todo:
        if processed >= BATCH:
            break
        hid = rec["hanreiId"]
        url = f"{PDF_BASE}hanrei-pdf-{hid}.pdf"
        try:
            r = requests.get(url, headers=HEADERS, timeout=60)
            r.raise_for_status()
            text = extract_text(io.BytesIO(r.content))
            result = extract_opinions(text)
            link_ids(result["individualOpinions"], jmap)
            panel = extract_panel(text)
            link_ids(panel, jmap)
            panel_ids = {p["judgeId"] for p in panel if p["judgeId"]}
            out = dict(rec)
            out.update(result)
            out["panel"] = panel
            out["hasActiveJudge"] = bool(panel_ids & active_ids)
            out["pdfTextLength"] = len(text)
            done[hid] = out
        except Exception as e:
            print(f"  失敗 {hid}: {type(e).__name__} {str(e)[:80]}", file=sys.stderr)
            done[hid] = dict(rec, individualOpinions=[], panel=[], hasActiveJudge=False,
                             needsReview=True, extractError=f"{type(e).__name__}")
        processed += 1
        if processed % 200 == 0:
            print(f"  ...{processed}件処理", file=sys.stderr)
        time.sleep(SLEEP)
    allrecs = sorted(done.values(), key=lambda x: int(x["hanreiId"]))
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    json.dump(allrecs, open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    remaining = len([r for r in src if r["hanreiId"] not in done])
    print(f"今回{processed}件 / 累計{len(done)}件 / 残り{remaining}件 を {OUT_JSON} に保存", file=sys.stderr)

if __name__ == "__main__":
    main()
