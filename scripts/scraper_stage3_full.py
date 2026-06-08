#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第3段（全件処理版）：Xserver公開URLからPDFを取得し、個別意見を抽出する。
- 入力: public/data/opinions_list_stage1.json（第1段の出力。hanreiId を持つ）
        public/data/judges.json（裁判官名簿。氏名→judgeId紐付け用）
- 処理: 各 hanreiId について Xserver の PDF を取得 → 個別意見抽出 → judgeId紐付け
- 出力: public/data/opinions_detail.json（個別意見付き）
- 分割実行: 既に opinions_detail.json にある hanreiId はスキップ。
            1回の実行で BATCH 件だけ処理（GitHub Actionsの6時間制限対策）。

環境変数:
  PDF_BASE   : PDFの公開URLベース（既定 https://cup1980.xsrv.jp/pdf/）
  BATCH      : 1回の実行で処理する件数（既定 2000）
  SLEEP      : 各PDF取得の間隔秒（既定 0.5）
実行前: pip install requests pdfminer.six
"""

import re, os, sys, json, io, time
import requests
from pdfminer.high_level import extract_text

PDF_BASE = os.environ.get("PDF_BASE", "https://cup1980.xsrv.jp/pdf/")
BATCH = int(os.environ.get("BATCH", "2000"))
SLEEP = float(os.environ.get("SLEEP", "0.5"))
HEADERS = {"User-Agent": "Mozilla/5.0 (SupremeCourtWatch; +github-actions)"}

LIST_JSON = "public/data/opinions_list_stage1.json"
JUDGES_JSON = "public/data/judges.json"
OUT_JSON = "public/data/opinions_detail.json"

# --- 抽出ロジック（検証済み・3件で確認） ---
HEADING_RE = re.compile(
    r"裁判官([^\sの、。]+?)の(追加反対意見|追加補足意見|反対意見|補足意見|意見)は、次のとおりである。")
SUMMARY_MENTION_RE = re.compile(
    r"裁判官([^\sの、。]+?)の(追加反対意見|追加補足意見|反対意見|補足意見|意見)が(?:ある|あった)")
UNANIMOUS_RE = re.compile(r"裁判官全員一致の意見")
PANEL_RE = re.compile(r"[（(]裁判長裁判官")

def normalize(text):
    return re.sub(r"-\s*\d+\s*-", "", text)

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
    return {
        "unanimous": unanimous,
        "individualOpinions": opinions,
        "needsReview": needs_review,
    }

def load_judges_map():
    """nameNormalized → judgeId の辞書"""
    if not os.path.exists(JUDGES_JSON):
        return {}
    judges = json.load(open(JUDGES_JSON, encoding="utf-8"))
    return {j["nameNormalized"]: j["judgeId"] for j in judges}

def link_judge_ids(opinions, judges_map):
    for o in opinions:
        norm = o["judge"].replace(" ", "").replace("　", "")
        o["judgeId"] = judges_map.get(norm)  # 見つからなければNone（退官者等→後で都度追加）
    return opinions

def main():
    src = json.load(open(LIST_JSON, encoding="utf-8"))
    judges_map = load_judges_map()

    # 既存の出力を読み（分割実行：続きから）
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
            result["individualOpinions"] = link_judge_ids(result["individualOpinions"], judges_map)
            out = dict(rec)  # 第1段の情報を引き継ぐ
            out.update(result)
            out["pdfTextLength"] = len(text)
            done[hid] = out
        except Exception as e:
            print(f"  失敗 {hid}: {type(e).__name__} {str(e)[:80]}", file=sys.stderr)
            done[hid] = dict(rec, individualOpinions=[], needsReview=True,
                             extractError=f"{type(e).__name__}")
        processed += 1
        if processed % 100 == 0:
            print(f"  ...{processed}件処理", file=sys.stderr)
        time.sleep(SLEEP)

    # 出力（hanreiId順）
    allrecs = sorted(done.values(), key=lambda x: int(x["hanreiId"]))
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    json.dump(allrecs, open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"今回{processed}件処理 / 累計{len(done)}件 を {OUT_JSON} に保存", file=sys.stderr)
    # 残りがあるかを終了コードで示す（0=全件完了, 10=まだ残あり）
    remaining = len([r for r in src if r["hanreiId"] not in done])
    print(f"残り{remaining}件", file=sys.stderr)

if __name__ == "__main__":
    main()
