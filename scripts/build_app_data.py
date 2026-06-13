#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_app_data.py（v1）
アプリ同梱用のデータを public/app-data/ に生成する。

入力（public/data/）:
  opinions_detail.json, opinions_summary.json, judges.json, judge_index.json
出力（public/app-data/）:
  judges.json            … 判事一覧（コピー）
  judge_index.json       … 判事→判例ID索引（コピー）
  cases_index.json       … 起動時に読む軽い判例一覧（検索/一覧用・URLは持たない）
  cases/<shard>.json      … 判例を開いた時に読む本文（要約全文＋個別意見）。
                            shard = int(hanreiId) % SHARDS。1ファイル数百KB程度。
  meta.json              … 件数・SHARDS・生成日時（アプリはこれで shard 数を知る）

URLはhanreiIdから復元できるので同梱しない（アプリ側で生成）:
  PDF   : https://www.courts.go.jp/assets/hanrei/hanrei-pdf-<id>.pdf
  詳細  : https://www.courts.go.jp/hanrei/<id>/detail2/index.html

環境変数: SHARDS（既定 50）
実行前: 標準ライブラリのみ（追加インストール不要）
"""
import json, os, sys, datetime

SRC = "public/data"
OUT = "public/app-data"
SHARDS = int(os.environ.get("SHARDS", "50"))

def load(name):
    p = os.path.join(SRC, name)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None

def main():
    detail = load("opinions_detail.json") or []
    summary = load("opinions_summary.json") or []
    judges = load("judges.json") or []
    judge_index = load("judge_index.json") or {}

    # 要約を hanreiId で引けるように
    smap = {}
    for r in summary:
        s = r.get("aiSummary") or {}
        smap[str(r.get("hanreiId"))] = s

    os.makedirs(os.path.join(OUT, "cases"), exist_ok=True)

    cases_index = []
    shard_data = {i: {} for i in range(SHARDS)}

    for r in detail:
        hid = str(r.get("hanreiId"))
        ops = r.get("individualOpinions") or []
        s = smap.get(hid, {})
        # --- 軽い索引（起動時）---
        cases_index.append({
            "id": hid,
            "name": r.get("caseName"),
            "no": r.get("caseNumber"),
            "date": r.get("date"),
            "field": r.get("field"),
            "outcome": r.get("outcome"),
            "court": r.get("court"),
            "div": r.get("division"),
            "opi": len(ops),                                   # 個別意見の数
            "dis": any(o.get("opinionType") == "反対意見" for o in ops),  # 反対意見の有無
            "tags": s.get("tags") or [],
        })
        # --- 本文（オンデマンド）---
        shard = int(hid) % SHARDS
        shard_data[shard][hid] = {
            "caseName": r.get("caseName"),
            "caseNumber": r.get("caseNumber"),
            "date": r.get("date"),
            "court": r.get("court"),
            "division": r.get("division"),
            "outcome": r.get("outcome"),
            "field": r.get("field"),
            "judgeKind": r.get("judgeKind"),
            "genshinCourt": r.get("genshinCourt"),
            "genshinCaseNumber": r.get("genshinCaseNumber"),
            "unanimous": r.get("unanimous"),
            "hasActiveJudge": r.get("hasActiveJudge"),
            "needsReview": r.get("needsReview"),
            "individualOpinions": ops,
            "concurrences": r.get("concurrences") or [],
            "panel": r.get("panel") or [],
            "summary": s.get("summary") or "",
            "summaryEasy": s.get("summaryEasy") or "",
            "legalPoint": s.get("legalPoint") or "",
            "dissent": s.get("dissent") or "",
            "summaryTags": s.get("tags") or [],
            "noText": bool(s.get("noText")),
        }

    # 書き出し
    json.dump(judges, open(os.path.join(OUT, "judges.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    json.dump(judge_index, open(os.path.join(OUT, "judge_index.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    json.dump(cases_index, open(os.path.join(OUT, "cases_index.json"), "w", encoding="utf-8"),
              ensure_ascii=False)  # 索引は最小化のため indent なし
    for i, dat in shard_data.items():
        json.dump(dat, open(os.path.join(OUT, "cases", f"{i}.json"), "w", encoding="utf-8"),
                  ensure_ascii=False)
    meta = {
        "cases": len(detail),
        "judges": len(judges),
        "shards": SHARDS,
        "builtAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "pdfBase": "https://www.courts.go.jp/assets/hanrei/hanrei-pdf-",
        "detailBase": "https://www.courts.go.jp/hanrei/",
    }
    json.dump(meta, open(os.path.join(OUT, "meta.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    # サイズ報告
    def mb(p):
        return os.path.getsize(p) / 1024 / 1024
    idx_mb = mb(os.path.join(OUT, "cases_index.json"))
    shard_sizes = [mb(os.path.join(OUT, "cases", f"{i}.json")) for i in range(SHARDS)]
    print(f"判例 {len(detail)}件 / 判事 {len(judges)}名 / shard {SHARDS}", file=sys.stderr)
    print(f"cases_index.json: {idx_mb:.2f} MB（起動時）", file=sys.stderr)
    print(f"cases/*.json    : 平均 {sum(shard_sizes)/len(shard_sizes):.2f} MB / 最大 {max(shard_sizes):.2f} MB（判例を開いた時）", file=sys.stderr)

if __name__ == "__main__":
    main()
