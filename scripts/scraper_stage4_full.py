#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第4段（全件処理版）v4：判例をAI要約する。
v4変更: RateLimitError時に自動リトライ（最大3回、60/120/180s待機）

- 入力: public/data/opinions_detail.json（第3段の出力）
- 各判例: XserverのPDF取得 → 要点抽出 → モデル振り分け → 要約5項目を生成
- モデル振り分け: hasActiveJudge=true → Sonnet（質重視）、false → Haiku（コスト）
- 出力5項目: summary / summaryEasy / legalPoint / dissent / tags
- 出力先: public/data/opinions_summary.json
- 分割実行: 既処理スキップ。1回 BATCH 件。50件ごとに途中保存。

環境変数: ANTHROPIC_API_KEY, PDF_BASE, BATCH, SLEEP,
          MODEL_ACTIVE(既定 claude-sonnet-4-6), MODEL_OTHER(既定 claude-haiku-4-5-20251001)
実行前: pip install anthropic requests pdfminer.six
"""
import os, sys, json, io, re, time
import requests
import anthropic
from anthropic import RateLimitError
from pdfminer.high_level import extract_text

PDF_BASE    = os.environ.get("PDF_BASE", "https://cup1980.xsrv.jp/pdf/")
BATCH       = int(os.environ.get("BATCH", "500"))
SLEEP       = float(os.environ.get("SLEEP", "0.2"))
MODEL_ACTIVE = os.environ.get("MODEL_ACTIVE", "claude-sonnet-4-6")
MODEL_OTHER  = os.environ.get("MODEL_OTHER",  "claude-haiku-4-5-20251001")
HEADERS = {"User-Agent": "Mozilla/5.0 (SupremeCourtWatch; +github-actions)"}

DETAIL_JSON = "public/data/opinions_detail.json"
OUT_JSON    = "public/data/opinions_summary.json"

TAGS = ["憲法・人権","家族法","労働","税務","選挙","社会保障","知的財産",
        "倒産・債権","不動産・借地借家","損害賠償・交通","消費者","出入国・難民"]

SYSTEM = """あなたは日本の最高裁判例を一般市民にわかりやすく伝える編集者です。
正確さを最優先し、判決文に書かれていないことは推測で補いません。
当事者名はPDFの通り（A・Xなど匿名は匿名のまま）扱います。
指定のJSON形式のみを出力し、前後に説明やマークダウン記号を付けません。"""

PROMPT = """次の最高裁判例の要点をもとに要約してください。

# 判例情報
- 事件名: {caseName}
- 法廷: {court}{division}
- 種別: {judgeKind}
- 結果: {outcome}
- 大分類: {field}
- 個別意見: {opinionsInfo}

# 判決の要点（本文から抽出）
{gist}

# 出力（このJSON形式のみ。説明やマークダウンは付けない）
{{
  "summary": "一般向け要約。新聞記事調で簡潔・正確に。2〜3文。何が争われ最高裁がどう判断したか。",
  "summaryEasy": "やさしい解説。専門用語をかみくだく。事実は正確に。2〜4文。",
  "legalPoint": "法的ポイント。争点と判断の核心を正確な用語で。1〜2文。",
  "dissent": "反対意見の簡潔な要約（誰がどういう論旨か）2〜3文。反対意見がなければ空文字。",
  "tags": ["テーマタグを次から1〜3個（該当なしは空配列）: {tags}"]
}}"""


# ── 要点抽出 ──────────────────────────────────────────────────────────────

def normalize(t):
    return re.sub(r"-\s*\d+\s*-", "", t)

def extract_gist(text, max_chars=1800):
    text = normalize(text)
    cut = re.search(
        r"裁判官[^の、。，]+?の(?:追加)?(?:反対意見|補足意見|意見)は[、，]\s*次のとおりである[。．]", text)
    main = text[:cut.start()] if cut else text

    shubun = ""
    ms = re.search(r"主\s*文\s*(.{10,300}?)\s*理\s*由", text, re.S)
    if ms:
        shubun = re.sub(r"\s+", " ", ms.group(1)).strip()

    mj = re.search(r"(本件は[、，].{20,400}?事案である[。．])", main, re.S)
    jian = mj.group(1) if mj else ""

    mc = re.search(
        r"((?:以上によれば|よって[、，]).{10,500}?"
        r"(?:主文のとおり[^。．]*[。．]|破棄を免れない[。．]|棄却すべきである[。．]))", main, re.S)
    concl = mc.group(1) if mc else ""

    g = "\n".join(filter(None, [
        ("【主文】" + shubun) if shubun else "",
        ("【事案】" + jian)   if jian   else "",
        ("【結論】" + concl)  if concl  else "",
    ]))
    # フォールバック: 定型句が拾えず gist が短い（古い様式・事件名空など）ときは
    # 本文先頭をそのまま渡す。これで「内容が無い」とAIに誤判定されるのを防ぐ。
    if len(g) < 100:
        body = re.sub(r"\s+", " ", main).strip()
        excerpt = "【本文抜粋】" + body[:1500]
        g = (g + "\n" + excerpt).strip() if g else excerpt
    return g[:max_chars]


# ── API呼び出し ──────────────────────────────────────────────────────────

def opinions_info(rec):
    ops = rec.get("individualOpinions", [])
    if not ops:
        return "なし（全員一致）"
    return "、".join(f"裁判官{o['judge']}の{o['opinionType']}" for o in ops)

def summarize(client, model, rec, gist):
    prompt = PROMPT.format(
        caseName=rec.get("caseName", ""),
        court=rec.get("court", ""),
        division=rec.get("division", "") or "",
        judgeKind=rec.get("judgeKind", ""),
        outcome=rec.get("outcome", "") or "（記載なし）",
        field=rec.get("field", "") or "（不明）",
        opinionsInfo=opinions_info(rec),
        gist=gist,
        tags="/".join(TAGS),
    )

    # v4: RateLimitError リトライ（最大3回、60/120/180s待機）
    msg = None
    for attempt in range(3):
        try:
            msg = client.messages.create(
                model=model, max_tokens=1200, system=SYSTEM,
                messages=[{"role": "user", "content": prompt}])
            break
        except RateLimitError:
            wait = 60 * (attempt + 1)
            print(f"  RateLimit、{wait}s待機してリトライ ({attempt + 1}/3)...",
                  file=sys.stderr)
            time.sleep(wait)
    if msg is None:
        raise RuntimeError("RateLimit: 3回リトライ後も失敗")

    text = msg.content[0].text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text).strip()
    if not text:
        raise ValueError("空応答（モデル名/残高/権限を確認）")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.S)
        if not m:
            raise ValueError(f"JSON抽出失敗: {text[:120]}")
        data = json.loads(m.group(0))

    data["tags"] = [t for t in data.get("tags", []) if t in TAGS][:3]
    return data


# ── メイン ───────────────────────────────────────────────────────────────

def save(done):
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    json.dump(
        sorted(done.values(), key=lambda x: int(x["hanreiId"])),
        open(OUT_JSON, "w", encoding="utf-8"),
        ensure_ascii=False, indent=2)

def main():
    detail = json.load(open(DETAIL_JSON, encoding="utf-8"))
    done = {}
    if os.path.exists(OUT_JSON):
        for r in json.load(open(OUT_JSON, encoding="utf-8")):
            done[r["hanreiId"]] = r
    todo = [r for r in detail if r["hanreiId"] not in done]
    print(f"全{len(detail)} / 済{len(done)} / 残{len(todo)} / 今回最大{BATCH}",
          file=sys.stderr)

    client = anthropic.Anthropic()
    processed = 0

    for rec in todo:
        if processed >= BATCH:
            break
        hid = rec["hanreiId"]
        model = MODEL_ACTIVE if rec.get("hasActiveJudge") else MODEL_OTHER
        try:
            r = requests.get(
                f"{PDF_BASE}hanrei-pdf-{hid}.pdf", headers=HEADERS, timeout=60)
            r.raise_for_status()
            gist = extract_gist(extract_text(io.BytesIO(r.content)))
            summary = summarize(client, model, rec, gist)
            out = dict(rec)
            out["aiSummary"] = summary
            out["model"] = model
            if summary.get("needsSummaryReview"):
                out["needsSummaryReview"] = True
            done[hid] = out
        except Exception as e:
            print(f"  失敗 {hid}: {type(e).__name__} {str(e)[:120]}", file=sys.stderr)
            done[hid] = dict(rec, aiSummary=None,
                             needsSummaryReview=True,
                             summaryError=f"{type(e).__name__}: {str(e)[:80]}")

        processed += 1
        if processed % 50 == 0:
            print(f"  ...{processed}件 / 累計{len(done)}", file=sys.stderr)
            save(done)  # 途中保存
        time.sleep(SLEEP)

    save(done)
    remaining = len([r for r in detail if r["hanreiId"] not in done])
    print(f"今回{processed}件 / 累計{len(done)} / 残り{remaining} を {OUT_JSON}",
          file=sys.stderr)

if __name__ == "__main__":
    main()
