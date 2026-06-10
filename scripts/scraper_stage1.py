# -*- coding: utf-8 -*-
"""
事件番号 ↔ 事件名 の分離 + 符号からの分野(field)判定（共通モジュール）。

これから取得するデータ（scraper_stage1.py）と、既存データのパッチ修正の
両方からこのモジュールを import して使う（ロジックを一箇所に集約）。

主な対応:
- 「新」付き表記（昭和24前後の旧→新刑訴移行期）。符号の前後どちらでも許容。
  例: 「昭和24新(れ)519」「昭和24(れ)新519」
- get_text 由来の改行・連続空白の混入を吸収。
- 明治〜令和、「年」「第」「号」「等」の有無を許容。
"""
import re

# 事件符号 → 分野(field) 一次分類（最高裁分）
CODE_TO_FIELD = {
    # 民事系
    "オ": "民事", "受": "民事", "許": "民事", "ク": "民事", "テ": "民事",
    "マ": "民事", "ヤ": "民事",
    # 行政系
    "行ツ": "行政", "行ヒ": "行政", "行フ": "行政", "行テ": "行政",
    "行ト": "行政", "行ナ": "行政", "行ニ": "行政",
    # 刑事系
    "あ": "刑事", "し": "刑事", "き": "刑事", "さ": "刑事", "す": "刑事",
    "せ": "刑事", "み": "刑事", "め": "刑事", "も": "刑事", "ゆ": "刑事",
    "れ": "刑事", "医へ": "刑事", "ひ": "刑事",
}

_GENGO = r"(?:明治|大正|昭和|平成|令和)"

# 事件番号フル: 元号+年(+新)+(符号)(+新)+番号
# 「新」は符号の前(昭和24新(れ)519)・後(昭和24(れ)新519)どちらも許容
CASE_NO_FULL = re.compile(
    _GENGO + r"(?:\d+|元)年?\s*"   # 元号 + 年（"元年"も）
    r"(?:新)?\s*"                  # 符号前の「新」
    r"\([^)]+\)\s*"               # 符号 (れ) (受) (行ツ) など
    r"(?:新)?\s*第?\s*\d+\s*号?(?:等)?"  # 符号後の「新」+ 番号
)

# field 判定用に符号だけを取り出す
CODE_RE = re.compile(
    _GENGO + r"(?:\d+|元)年?\s*(?:新)?\s*\(([^)]+)\)"
)


def split_case_number_name(line1):
    """『平成30(受)1874 請求異議事件』→ ('平成30(受)1874', '請求異議事件')

    改行・連続空白を畳んでから事件番号を切り出す。マッチしない場合は
    行全体を caseNumber、caseName を空で返す（従来挙動を踏襲）。
    """
    line1 = re.sub(r"\s+", " ", line1 or "").strip()
    m = CASE_NO_FULL.match(line1)
    if m:
        case_number = re.sub(r"\s+", "", m.group(0))  # 事件番号内の空白除去
        case_name = line1[m.end():].strip()
        return case_number, case_name
    return line1, ""


def field_from_case_number(case_number):
    """事件番号の符号から分野を一次判定。未知符号・抽出失敗は None。"""
    m = CODE_RE.search(case_number or "")
    if not m:
        return None
    return CODE_TO_FIELD.get(m.group(1).strip())


def repair_record(rec):
    """既存レコードのパッチ用。caseName が空 or caseNumber に事件名が
    巻き込まれている場合に、caseNumber/caseName/field を整える。
    変更があったら True を返す（再処理対象の判定に使える）。
    """
    changed = False
    raw = rec.get("caseNumber", "") or ""
    name = rec.get("caseName", "") or ""

    # caseNumber に空白/改行混入、または caseName が空のとき分離を試みる
    if (not name) or re.search(r"\s", raw):
        cn, nm = split_case_number_name(raw if not name else f"{raw} {name}")
        if cn != raw:
            rec["caseNumber"] = cn
            changed = True
        if nm and nm != name:
            rec["caseName"] = nm
            changed = True

    # field が空なら符号から補完
    if not rec.get("field"):
        f = field_from_case_number(rec.get("caseNumber", ""))
        if f:
            rec["field"] = f
            changed = True

    return changed
