#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第1段の出力JSON（opinions_list_stage1.json）から CSV を生成する。
列: hanreiId, caseNumber, caseName, date, court, division, judgeKind,
    outcome, field, genshinCourt, genshinCaseNumber, fullTextPdf, detailUrl
- Excelで文字化けしないよう BOM付きUTF-8 (utf-8-sig) で出力。
- wgetに渡すときは fullTextPdf 列だけ抜けばよい。

使い方:
  python make_csv.py opinions_list_stage1.json opinions_list_stage1.csv
"""
import json, csv, sys

COLUMNS = [
    "hanreiId", "caseNumber", "caseName", "date", "court", "division",
    "judgeKind", "outcome", "field", "genshinCourt", "genshinCaseNumber",
    "fullTextPdf", "detailUrl",
]

def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "opinions_list_stage1.json"
    dst = sys.argv[2] if len(sys.argv) > 2 else "opinions_list_stage1.csv"
    data = json.load(open(src, encoding="utf-8"))
    with open(dst, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        w.writeheader()
        for rec in data:
            w.writerow({c: (rec.get(c) or "") for c in COLUMNS})
    print(f"{len(data)} 行を {dst} に出力")

if __name__ == "__main__":
    main()
