#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
既存データの事件名パッチ（patch-casenum ワークフローから実行）。

casenum.repair_record を使い、以下3ファイルの caseNumber/caseName/field を
そろえる。第1段(scrape-list-csv)を作り直しても下流(stage3/stage4)は
「処理済みスキップ」で古いままになるため、ここで直接そろえる。

対象:
  public/data/opinions_list_stage1.json
  public/data/opinions_detail.json
  public/data/opinions_summary.json

モード（環境変数 DRY_RUN）:
  "true"（既定） … 下見。何件直るか集計表示するだけで書き込まない。
  "false"        … 実際に修正して保存。caseName を新たに復旧した hanreiId を
                   public/data/recheck_after_patch.json に書き出す
                   （= stage4-summary で再要約すべき候補）。

依存: 標準ライブラリ + casenum.py のみ（pip install 不要）。
casenum.py を同じ scripts/ フォルダに置くこと。
"""
import os, sys, json
import casenum

TARGETS = [
    "public/data/opinions_list_stage1.json",
    "public/data/opinions_detail.json",
    "public/data/opinions_summary.json",
]
RECHECK_OUT = "public/data/recheck_after_patch.json"


def process_file(path, dry_run):
    """1ファイルを処理。(変更件数, caseName復旧件数, field補完件数, 復旧したid集合) を返す。"""
    if not os.path.exists(path):
        print(f"  [skip] {path} が見つかりません")
        return 0, 0, 0, set()

    data = json.load(open(path, encoding="utf-8"))
    changed = name_recovered = field_recovered = 0
    recovered_ids = set()
    samples = []

    for rec in data:
        before_name = (rec.get("caseName") or "").strip()
        before_field = rec.get("field")
        if casenum.repair_record(rec):
            changed += 1
            recovered_name = (not before_name) and bool((rec.get("caseName") or "").strip())
            if recovered_name:
                name_recovered += 1
                recovered_ids.add(rec.get("hanreiId"))
            if (not before_field) and rec.get("field"):
                field_recovered += 1
            if len(samples) < 5:
                samples.append((rec.get("hanreiId"), rec.get("caseNumber"), rec.get("caseName")))

    print(f"  {path}: 全{len(data)}件 / 変更{changed}件 "
          f"（caseName復旧{name_recovered} / field補完{field_recovered}）")
    for hid, cn, nm in samples:
        print(f"     例 id={hid}  {cn}  →  {nm}")

    if not dry_run and changed:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"     保存しました: {path}")

    return changed, name_recovered, field_recovered, recovered_ids


def main():
    dry_run = os.environ.get("DRY_RUN", "true").lower() != "false"
    mode = "下見（DRY-RUN：書き込みません）" if dry_run else "実行（修正を保存します）"
    print(f"=== patch-casenum / モード: {mode} ===\n")

    total_changed = 0
    all_recovered = set()
    for path in TARGETS:
        c, _, _, ids = process_file(path, dry_run)
        total_changed += c
        all_recovered |= ids

    all_recovered.discard(None)
    print(f"\n合計 変更{total_changed}件 / caseName を復旧した判例 {len(all_recovered)}件")

    if dry_run:
        print("\n下見の結果に問題がなければ、DRY_RUN=false で再実行してください。")
    else:
        os.makedirs(os.path.dirname(RECHECK_OUT), exist_ok=True)
        with open(RECHECK_OUT, "w", encoding="utf-8") as f:
            json.dump(sorted(all_recovered), f, ensure_ascii=False, indent=2)
        print(f"\n再要約候補（caseName復旧分）を {RECHECK_OUT} に保存しました。")
        print("→ 次段（stage4-summary の再処理）で、このIDの要約を作り直します。")


if __name__ == "__main__":
    main()
