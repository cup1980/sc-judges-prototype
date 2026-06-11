#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
再要約が必要なレコードを opinions_summary.json から削除し、stage4-submit が
未処理として拾えるようにする（処理済みスキップ設計のため、消さないと再要約されない）。

対象（いずれか）:
  - recheck_after_patch.json に載っている（事件名修正・第3段再抽出で内容が変わった）
  - needsSummaryReview=true
  - 要約本文が空
  - summaryError あり（parse失敗など）

stage4-submit の reset_resummary=true 実行時に、submit の前に呼ばれる。
"""
import json, os

SUMMARY = "public/data/opinions_summary.json"
RECHECK = "public/data/recheck_after_patch.json"


def main():
    if not os.path.exists(SUMMARY):
        print(f"{SUMMARY} がありません。")
        return
    data = json.load(open(SUMMARY, encoding="utf-8"))

    recheck = set()
    if os.path.exists(RECHECK):
        try:
            recheck = set(json.load(open(RECHECK, encoding="utf-8")))
        except Exception:
            recheck = set()

    def needs_redo(r):
        s = r.get("aiSummary") or {}
        return (
            r.get("hanreiId") in recheck
            or r.get("needsSummaryReview")
            or s.get("needsSummaryReview")
            or not (s.get("summary") or "").strip()
            or bool(r.get("summaryError"))
        )

    before = len(data)
    targets = [r["hanreiId"] for r in data if needs_redo(r)]
    kept = [r for r in data if not needs_redo(r)]
    json.dump(kept, open(SUMMARY, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    print(f"再要約対象 {len(targets)}件を削除（summary {before}→{len(kept)}）")
    print("→ stage4-submit でこの件が再要約されます。")


if __name__ == "__main__":
    main()
