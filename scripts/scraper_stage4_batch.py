#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第4段 Batch版: Message Batches API で要約（50%オフ・非同期）。

MODE=submit : 未処理を選び、PDF取得→gist抽出→プロンプト化してバッチ投入。
              batch_id を public/data/batch_state.json に保存。
MODE=collect: batch_id の結果を取得し summary にマージ。
              まだ処理中なら「処理中」と表示して終了（時間を置いて再実行）。

既存 scraper_stage4_full.py のロジック（gist抽出・プロンプト・保存）を import で流用。
scraper_stage4_full.py と同じ scripts/ に置くこと。

環境変数:
  MODE        : submit / collect（必須）
  TEST_LIMIT  : submitで投入する最大件数（0=未処理全部。試すときは 50 など）
  PDF_BASE, MODEL_ACTIVE, MODEL_OTHER（scraper_stage4_full と同じ既定を継承）
実行前: pip install anthropic requests pdfminer.six
"""
import os, sys, json, io, re
import requests as http
import anthropic
from pdfminer.high_level import extract_text

# 既存ロジックを流用（gist抽出・プロンプト・定数・保存）
from scraper_stage4_full import (
    extract_gist, opinions_info, SYSTEM, PROMPT, TAGS,
    PDF_BASE, MODEL_ACTIVE, MODEL_OTHER, DETAIL_JSON, OUT_JSON, save,
)

HEADERS = {"User-Agent": "Mozilla/5.0 (SupremeCourtWatch; +github-actions)"}
STATE_JSON = "public/data/batch_state.json"


def build_prompt(rec):
    """PDFを取得して gist を抜き、プロンプト文字列を作る（同期版と同じ組み立て）。"""
    hid = rec["hanreiId"]
    r = http.get(f"{PDF_BASE}hanrei-pdf-{hid}.pdf", headers=HEADERS, timeout=60)
    r.raise_for_status()
    gist = extract_gist(extract_text(io.BytesIO(r.content)))
    return PROMPT.format(
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


def parse_summary(text):
    """同期版 summarize の後処理部分（```除去・JSON救出・tags矯正）を分離したもの。"""
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip()).strip()
    if not text:
        raise ValueError("空応答")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.S)
        if not m:
            raise ValueError(f"JSON抽出失敗: {text[:120]}")
        data = json.loads(m.group(0))
    data["tags"] = [t for t in data.get("tags", []) if t in TAGS][:3]
    return data


def load_done():
    done = {}
    if os.path.exists(OUT_JSON):
        for r in json.load(open(OUT_JSON, encoding="utf-8")):
            done[r["hanreiId"]] = r
    return done


# ── submit ───────────────────────────────────────────────────────────────

def submit(client):
    limit = int(os.environ.get("TEST_LIMIT", "0"))
    detail = json.load(open(DETAIL_JSON, encoding="utf-8"))
    done = load_done()
    todo = [r for r in detail if r["hanreiId"] not in done]
    if limit:
        todo = todo[:limit]
    print(f"未処理から {len(todo)} 件を投入準備（PDF取得中）...", file=sys.stderr)

    reqs, skipped = [], []
    for i, rec in enumerate(todo, 1):
        hid = rec["hanreiId"]
        try:
            prompt = build_prompt(rec)
        except Exception as e:
            skipped.append(hid)
            print(f"  PDF取得失敗 {hid}: {type(e).__name__}", file=sys.stderr)
            continue
        model = MODEL_ACTIVE if rec.get("hasActiveJudge") else MODEL_OTHER
        reqs.append({
            "custom_id": f"h{hid}",
            "params": {
                "model": model,
                "max_tokens": 1200,
                "system": SYSTEM,
                "messages": [{"role": "user", "content": prompt}],
            },
        })
        if i % 100 == 0:
            print(f"  ...{i}/{len(todo)} 準備済", file=sys.stderr)

    if not reqs:
        print("投入対象がありません。")
        return
    batch = client.messages.batches.create(requests=reqs)
    os.makedirs(os.path.dirname(STATE_JSON), exist_ok=True)
    json.dump(
        {"batch_id": batch.id, "submitted": len(reqs), "skipped": skipped},
        open(STATE_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"投入完了: batch_id={batch.id} / {len(reqs)}件 / PDF取得失敗{len(skipped)}件")
    print("→ 1時間ほど置いてから stage4-collect を実行してください。")


# ── collect ──────────────────────────────────────────────────────────────

def collect(client):
    if not os.path.exists(STATE_JSON):
        print("batch_state.json がありません。先に submit してください。", file=sys.stderr)
        sys.exit(1)
    batch_id = json.load(open(STATE_JSON, encoding="utf-8"))["batch_id"]
    b = client.messages.batches.retrieve(batch_id)
    print(f"batch {batch_id} / status={b.processing_status} / {b.request_counts}",
          file=sys.stderr)
    if b.processing_status != "ended":
        print("まだ処理中です。しばらく置いてから再実行してください。")
        return

    detail = {r["hanreiId"]: r for r in json.load(open(DETAIL_JSON, encoding="utf-8"))}
    done = load_done()
    ok = err = 0
    for entry in client.messages.batches.results(batch_id):
        hid = entry.custom_id[1:]          # 先頭 "h" を除去
        rec = detail.get(hid)
        if not rec:
            continue
        model = MODEL_ACTIVE if rec.get("hasActiveJudge") else MODEL_OTHER
        if entry.result.type == "succeeded":
            try:
                text = entry.result.message.content[0].text
                summary = parse_summary(text)
                out = dict(rec)
                out["aiSummary"] = summary
                out["model"] = model
                if summary.get("needsSummaryReview"):
                    out["needsSummaryReview"] = True
                done[hid] = out
                ok += 1
            except Exception as e:
                done[hid] = dict(rec, aiSummary=None, needsSummaryReview=True,
                                 summaryError=f"parse: {str(e)[:80]}")
                err += 1
        else:
            done[hid] = dict(rec, aiSummary=None, needsSummaryReview=True,
                             summaryError=str(entry.result.type))
            err += 1

    save(done)
    remaining = sum(1 for r in detail.values() if r["hanreiId"] not in done)
    print(f"取得完了: 成功{ok} / 失敗{err} / 累計{len(done)} / 残り{remaining}")


def main():
    mode = os.environ.get("MODE", "").lower()
    client = anthropic.Anthropic()
    if mode == "submit":
        submit(client)
    elif mode == "collect":
        collect(client)
    else:
        print("MODE=submit か MODE=collect を指定してください。", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
