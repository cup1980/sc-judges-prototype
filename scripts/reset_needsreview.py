#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
needsReview=true のレコードを opinions_detail.json から削除し、stage3 で
再抽出できるようにする（処理済みスキップ設計のため、消さないと再処理されない）。

削除した hanreiId は recheck_after_patch.json に追記する。再抽出で個別意見が
変わる可能性が高く、第4段（要約）でも作り直す候補になるため。

stage3-opinions の reset_needs_review=true 実行時に、抽出の前に呼ばれる。
"""
import json, os

DETAIL = "public/data/opinions_detail.json"
RECHECK = "public/data/recheck_after_patch.json"


def main():
    if not os.path.exists(DETAIL):
        print(f"{DETAIL} がありません。")
        return
    data = json.load(open(DETAIL, encoding="utf-8"))
    before = len(data)
    targets = [r["hanreiId"] for r in data if r.get("needsReview")]
    kept = [r for r in data if not r.get("needsReview")]
    json.dump(kept, open(DETAIL, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    # 再要約候補に統合（重複排除）
    existing = []
    if os.path.exists(RECHECK):
        try:
            existing = json.load(open(RECHECK, encoding="utf-8"))
        except Exception:
            existing = []
    merged = sorted(set(existing) | set(targets))
    os.makedirs(os.path.dirname(RECHECK), exist_ok=True)
    json.dump(merged, open(RECHECK, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    print(f"needsReview=true を {len(targets)}件削除（detail {before}→{len(kept)}）")
    print(f"→ stage3 がこの {len(targets)}件を未処理として再抽出します。")
    print(f"再要約候補 recheck_after_patch.json: 計{len(merged)}件")


if __name__ == "__main__":
    main()
