#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第3段（v3）：XserverのPDFから個別意見＋裁判官名簿を抽出する。
v2からの変更点（needsReview 誤検知の解消）:
  - 結語の突合パーサを「列挙形」に対応：
      「裁判官A、同B〔、同C〕の〔各〕…意見がある」のように 同 で連ねた
      共同意見を、全員ぶん展開して拾う（P1）。
  - 意見タイプ語の内部改行に対応：「補足\n\n意見」のようにページ/行で
      割れても「補足意見」と認識（P2。タイプ正規表現に \\s* を許容）。
  - 同調裁判官を検出：「裁判官Xは、裁判官Yの…意見に同調する」を concurrences
      として記録。X は自前の本文を持たないので needsReview の対象外にする（P3）。
  - needsReview の判定を見直し：
      「結語で予告されたのに、本文も同調も無い意見」がある場合だけ true。
      本文の方が多い（結語パーサの取りこぼし）方向は誤検知なので flag しない。
  - ITAIJI に 德→徳 を追加（P4の一部。ただし字形ずれで名前自体が崩れる
      ケースの judgeId 紐付けは別途要対応）。
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

# 意見タイプ語（内部に空白/改行が割り込んでも一致するよう \s* を許容）
TYPE = r"(?:追\s*加\s*)?(?:反\s*対|補\s*足)?\s*意\s*見"
# 名前：の/読点/句点を含まない（空白・改行は名前内に許容し、後で norm_name で除去）
NAME = r"[^、。，の]{1,20}?"

# 本文の見出し「裁判官○○の△△意見は、次のとおりである。」
HEADING_RE = re.compile(
    r"裁判官\s*(" + NAME + r")\s*の\s*(" + TYPE + r")\s*は[、，]\s*次のとおりである[。．]")

# 結語の列挙形「裁判官A、同B〔、同C〕の〔各〕…意見」（…意見の直後が
#   「があ(る/った)」/「、裁判官」/「。」のいずれかであることを要求）
CLAUSE_RE = re.compile(
    r"裁判官\s*(" + NAME + r"(?:\s*[、，]\s*同\s*" + NAME + r")*)\s*の\s*(?:各\s*)?"
    r"(" + TYPE + r")"
    r"(?=\s*(?:があ|[、，]\s*裁判官|[。．]))")

# 同調「裁判官Xは、裁判官Yの〔右〕…意見〔中の…〕に同調する」
CONCUR_RE = re.compile(
    r"裁判官\s*(" + NAME + r")\s*は[、，]\s*裁判官\s*(" + NAME + r")\s*の\s*(?:右\s*)?"
    r"(" + TYPE + r")(?:[^。．]{0,20})?に\s*同\s*調\s*する")

UNANIMOUS_RE = re.compile(r"裁判官全員一致の意見")
PANEL_RE = re.compile(r"[（(]\s*裁\s*判\s*長\s*裁\s*判\s*官(.+?)[）)]", re.S)

ITAIJI = str.maketrans({"邉":"辺","邊":"辺","惠":"恵","眞":"真","槇":"槙","德":"徳"})

def normalize(text):
    return re.sub(r"-\s*\d+\s*-", "", text)

def norm_name(name):
    n = re.sub(r"\s+", "", name or "")   # 半角/全角スペース・改行をすべて除去
    return n.translate(ITAIJI)

def canon_type(s):
    return re.sub(r"\s+", "", s or "")

def _split_chain(name_block):
    # 「A、同B、同C」→ [A, B, C]
    parts = re.split(r"[、，]\s*同\s*", name_block)
    return [p for p in (norm_name(x) for x in parts) if p and "全員" not in p]

def extract_opinions(text):
    text = normalize(text)
    unanimous = bool(UNANIMOUS_RE.search(text))

    # 結語が予告する（裁判官, タイプ）の集合
    expected = set()
    for m in CLAUSE_RE.finditer(text):
        otype = canon_type(m.group(2))
        for nm in _split_chain(m.group(1)):
            expected.add((nm, otype))

    # 本文に実在する見出し
    headings = [(m.start(), norm_name(m.group(1)), canon_type(m.group(2)))
                for m in HEADING_RE.finditer(text)]
    body_set = {(j, t) for _, j, t in headings}

    # 同調（自前の本文を持たない）
    concurrences = []
    for m in CONCUR_RE.finditer(text):
        concurrences.append({"judge": norm_name(m.group(1)),
                             "withJudge": norm_name(m.group(2)),
                             "opinionType": canon_type(m.group(3))})
    concur_set = {(c["judge"], c["opinionType"]) for c in concurrences}

    # 本文ブロックの組み立て（従来どおり）
    panel_m = PANEL_RE.search(text)
    panel_pos = panel_m.start() if panel_m else len(text)
    opinions = []
    for i, (pos, judge, otype) in enumerate(headings):
        end = headings[i + 1][0] if i + 1 < len(headings) else (panel_pos if panel_pos > pos else len(text))
        body = text[pos:end].strip()
        opinions.append({"judge": judge, "opinionType": otype, "bodyLength": len(body)})

    # needsReview: 結語で予告されたのに本文も同調も無いものがある場合だけ true
    missing = expected - body_set - concur_set
    needs_review = bool(missing)
    result = {"unanimous": unanimous, "individualOpinions": opinions,
              "concurrences": concurrences, "needsReview": needs_review}
    if needs_review:
        result["reviewReason"] = [{"judge": j, "opinionType": t} for j, t in sorted(missing)]
    return result

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
        if "withJudge" in o:
            o["withJudgeId"] = jmap.get(norm_name(o.get("withJudge")))
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
            link_ids(result["concurrences"], jmap)
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
            done[hid] = dict(rec, individualOpinions=[], concurrences=[], panel=[],
                             hasActiveJudge=False, needsReview=True,
                             extractError=f"{type(e).__name__}")
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
