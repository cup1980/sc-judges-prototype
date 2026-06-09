#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
要チェック案件の一覧書き出し
- needsReview（第3段：個別意見抽出が曖昧）
- needsSummaryReview（第4段：AI要約が崩れた/失敗）
のいずれかが立った案件を抽出し、CSVに出す。

入力: public/data/opinions_summary.json（無ければ opinions_detail.json）
出力: public/data/review_list.csv
列: hanreiId, caseName, needsReview, needsSummaryReview, summaryError, fullTextPdf, detailUrl

使い方: python make_review_list.py
"""
import os, json, csv, sys

CANDIDATES = ["public/data/opinions_summary.json", "public/data/opinions_detail.json"]
OUT = "public/data/review_list.csv"

def main():
    src = next((p for p in CANDIDATES if os.path.exists(p)), None)
    if not src:
        print("入力JSONが見つかりません", file=sys.stderr); sys.exit(1)
    data = json.load(open(src, encoding="utf-8"))

    rows = []
    for r in data:
        nr = r.get("needsReview", False)
        nsr = r.get("needsSummaryReview", False)
        # aiSummary内にだけフラグがある場合も拾う
        ai = r.get("aiSummary") or {}
        if isinstance(ai, dict) and ai.get("needsSummaryReview"):
            nsr = True
        if nr or nsr:
            rows.append({
                "hanreiId": r.get("hanreiId",""),
                "caseName": r.get("caseName",""),
                "needsReview": "1" if nr else "",
                "needsSummaryReview": "1" if nsr else "",
                "summaryError": r.get("summaryError",""),
                "fullTextPdf": r.get("fullTextPdf",""),
                "detailUrl": r.get("detailUrl",""),
            })

    rows.sort(key=lambda x: int(x["hanreiId"]) if x["hanreiId"].isdigit() else 0)
    cols = ["hanreiId","caseName","needsReview","needsSummaryReview","summaryError","fullTextPdf","detailUrl"]
    with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    # 集計をログに
    nr_n = sum(1 for x in rows if x["needsReview"])
    nsr_n = sum(1 for x in rows if x["needsSummaryReview"])
    print(f"要チェック {len(rows)}件 (needsReview {nr_n} / needsSummaryReview {nsr_n}) → {OUT}", file=sys.stderr)

if __name__ == "__main__":
    main()
