#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第3段（v6）：XserverのPDFから個別意見＋裁判官名簿を抽出する。
v4からの変更点（残150件の3パターン対応）:
  - P5 連名の見出し：本文見出し「裁判官A、同B〔、同C〕の…意見は、次のとおりである」
      を連名対応にし、列挙された全員ぶんを本文集合に展開。
  - P5 連名の同調：「裁判官A、同Bは、裁判官Cの…意見に同調する」を全員ぶん記録。
  - P7 読点なしの見出し：古い判決の「は次のとおりである」（は直後の読点なし）に対応
      （読点を任意化）。
  - P6 ゴミ拾いの排除：結語の探索を「最初の個別意見見出しより前」だけに限定し、
      本文中の「○○裁判官にも，同旨の補足意見がある」等を結語と誤認しない。
      あわせて名前妥当性チェック（ひらがな/カタカナのみ・1文字を除外）を追加。
  - 連名見出しの個別意見は各裁判官ぶんのエントリを作り、jointWith に共著者を付す。
v6: PDF取得を自動リトライ化（ConnectTimeout等のXserver一時不調で落ちないように、
    指数バックオフで最大RETRIES回再試行。最終失敗時のみ extractError 記録）。
（v4までの確定事項）
  - needsReview = 結語が予告した集合 − 本文見出し集合 − 同調集合 が空でないとき true。
  - NAME_FIX で字形ずれ補正（泉治→泉徳治）。ITAIJI 変換。concurrences 出力。
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
RETRIES = int(os.environ.get("RETRIES", "4"))

LIST_JSON = "public/data/opinions_list_stage1.json"
JUDGES_JSON = "public/data/judges.json"
OUT_JSON = "public/data/opinions_detail.json"

# 意見タイプ語（内部に空白/改行が割り込んでも一致するよう \s* を許容）
TYPE = r"(?:追\s*加\s*)?(?:反\s*対|補\s*足)?\s*意\s*見"
# 名前：の/読点/句点を含まない（空白・改行は名前内に許容し、後で norm_name で除去）
NAME = r"[^、。，の]{1,20}?"
# 名前リスト「A、同B、同C」
NAMELIST = NAME + r"(?:\s*[、，]\s*同\s*" + NAME + r")*"

# 本文の見出し「裁判官〔A、同B…〕の△△意見は〔、〕次のとおりである。」
#   ※ 読点(は の直後)は任意（古い判決は読点なし）
HEADING_RE = re.compile(
    r"裁判官\s*(" + NAMELIST + r")\s*の\s*(" + TYPE + r")\s*は[、，]?\s*次のとおりである[。．]")

# 結語の列挙形「裁判官〔A、同B…〕の〔各〕…意見」
#   …意見の直後が「があ(る/った)」/「、裁判官」/「。」のいずれか
CLAUSE_RE = re.compile(
    r"裁判官\s*(" + NAMELIST + r")\s*の\s*(?:各\s*)?(" + TYPE + r")"
    r"(?=\s*(?:があ|[、，]\s*裁判官|[。．]))")

# 同調「裁判官〔A、同B…〕は、裁判官Cの〔右〕…意見〔中…〕に同調する」
CONCUR_RE = re.compile(
    r"裁判官\s*(" + NAMELIST + r")\s*は[、，]\s*裁判官\s*(" + NAME + r")\s*の\s*(?:右\s*)?"
    r"(" + TYPE + r")(?:[^。．]{0,20})?に\s*同\s*調\s*する")

UNANIMOUS_RE = re.compile(r"裁判官全員一致の意見")
PANEL_RE = re.compile(r"[（(]\s*裁\s*判\s*長\s*裁\s*判\s*官(.+?)[）)]", re.S)

ITAIJI = str.maketrans({"邉":"辺","邊":"辺","惠":"恵","眞":"真","槇":"槙","德":"徳"})

# PDF抽出で字形（外字）が位置ずれし名前から脱落する既知ケースの補正。
# 値は judges.json の正規表記。新たに見つかれば1行追加するだけ。
NAME_FIX = {"泉治": "泉徳治"}

def normalize(text):
    return re.sub(r"-\s*\d+\s*-", "", text)

def norm_name(name):
    n = re.sub(r"\s+", "", name or "").translate(ITAIJI)  # 空白除去＋異体字吸収
    return NAME_FIX.get(n, n)

def canon_type(s):
    return re.sub(r"\s+", "", s or "")

def is_valid_name(n):
    # 名前として不自然なゴミ（ひらがな/カタカナのみ・1文字・全員一致片）を除外
    if not n or len(n) < 2:
        return False
    if "全員" in n:
        return False
    if re.fullmatch(r"[ぁ-ん]+", n):
        return False
    if re.fullmatch(r"[ァ-ンー]+", n):
        return False
    return True

def split_names(name_block):
    # 「A、同B、同C」→ [A, B, C]（正規化＋妥当性フィルタ）
    parts = re.split(r"[、，]\s*同\s*", name_block)
    out = []
    for p in parts:
        nm = norm_name(p)
        if is_valid_name(nm):
            out.append(nm)
    return out

def extract_opinions(text):
    text = normalize(text)
    unanimous = bool(UNANIMOUS_RE.search(text))

    # 本文の見出し（連名対応）：(開始位置, [裁判官...], タイプ)
    heads = []
    for m in HEADING_RE.finditer(text):
        names = split_names(m.group(1))
        otype = canon_type(m.group(2))
        if names:
            heads.append((m.start(), names, otype))
    body_set = {(j, t) for _, names, t in heads for j in names}

    # 結語は「最初の個別意見見出しより前」だけを探索（本文中の言及をゴミ拾いしない）
    region_end = heads[0][0] if heads else len(text)
    conclusion = text[:region_end]
    expected = set()
    for m in CLAUSE_RE.finditer(conclusion):
        otype = canon_type(m.group(2))
        for nm in split_names(m.group(1)):
            expected.add((nm, otype))

    # 同調（連名対応・自前の本文を持たない）
    concurrences = []
    for m in CONCUR_RE.finditer(text):
        with_j = norm_name(m.group(2))
        otype = canon_type(m.group(3))
        for nm in split_names(m.group(1)):
            concurrences.append({"judge": nm, "withJudge": with_j, "opinionType": otype})
    concur_set = {(c["judge"], c["opinionType"]) for c in concurrences}

    # 本文ブロックの組み立て（連名は共著者を jointWith に）
    panel_m = PANEL_RE.search(text)
    panel_pos = panel_m.start() if panel_m else len(text)
    opinions = []
    for i, (pos, names, otype) in enumerate(heads):
        end = heads[i + 1][0] if i + 1 < len(heads) else (panel_pos if panel_pos > pos else len(text))
        blen = len(text[pos:end].strip())
        for nm in names:
            o = {"judge": nm, "opinionType": otype, "bodyLength": blen}
            if len(names) > 1:
                o["jointWith"] = [x for x in names if x != nm]
            opinions.append(o)

    # needsReview: 結語が予告したのに本文も同調も無いものがある場合だけ true
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

def fetch_pdf(url):
    # Xserverの一時不調（ConnectTimeout等）に備え指数バックオフで再試行
    last = None
    for i in range(RETRIES):
        try:
            r = requests.get(url, headers=HEADERS, timeout=60)
            r.raise_for_status()
            return r.content
        except Exception as e:
            last = e
            if i + 1 < RETRIES:
                time.sleep(3 * (i + 1))
    raise last

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
            content = fetch_pdf(url)
            text = extract_text(io.BytesIO(content))
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
