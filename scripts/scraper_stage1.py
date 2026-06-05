#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最高裁判例DB scraper 第1段（一覧クロール）
- courts.go.jp の最高裁タブ(search2, courtCaseType=1)を日付範囲×offsetで総当たり
- 各判例の: 判例ID/事件番号/事件名/裁判年月日/法廷/裁判種別/結果/原審/分野/全文PDF を抽出
- 正規化JSONを出力（後でDBに移せる形）
※ courts.go.jp は要ネットワーク接続。手元PCかGitHub Actionsで実行。
   実行前: pip install requests beautifulsoup4
"""

import requests, time, json, re, sys
from bs4 import BeautifulSoup
from urllib.parse import urlencode

BASE = "https://www.courts.go.jp/hanrei/search2/index.html"
HEADERS = {
    # 連絡先を入れておくと運営側に親切（任意で書き換え）
    "User-Agent": "Mozilla/5.0 (SupremeCourtWatch research bot; contact: example@example.com)"
}

# ------- 事件符号 → 分野(field) 一次分類（最高裁分） -------
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

# 事件番号から符号を取り出す: 例「平成30(受)1874」→「受」, 「令和2(行ヒ)102」→「行ヒ」
CASE_NO_RE = re.compile(r"(?:平成|令和|昭和)\d+\(([^)]+)\)\d+")

COURT_DIV_RE = re.compile(r"(大法廷|第一小法廷|第二小法廷|第三小法廷)")
JUDGE_KIND_RE = re.compile(r"(判決|決定)")
# 結果語（よく出るもの。必要に応じ追加）
RESULT_RE = re.compile(
    r"(破棄差戻|破棄自判|破棄移送|上告棄却|上告却下|棄却|却下|認容|変更|"
    r"原判決破棄|差戻|移送|取消)"
)
# 原審: 「○○高等裁判所 平成27(ネ)19」など（裁判所名＋事件番号）
GENSHIN_RE = re.compile(
    r"((?:[^\s]+?(?:高等裁判所|地方裁判所|家庭裁判所|簡易裁判所))[^\s]*)\s*"
    r"((?:平成|令和|昭和)\d+\([^)]+\)\d+(?:等)?)"
)


def build_url(g_from, y_from, m_from, d_from, g_to, y_to, m_to, d_to, offset=0):
    params = {
        "courtCaseType": "1",  # 最高裁のみ
        "filter[judgeDateMode]": "2",  # 期間指定
        "filter[judgeGengoFrom]": g_from, "filter[judgeYearFrom]": y_from,
        "filter[judgeMonthFrom]": m_from, "filter[judgeDayFrom]": d_from,
        "filter[judgeGengoTo]": g_to, "filter[judgeYearTo]": y_to,
        "filter[judgeMonthTo]": m_to, "filter[judgeDayTo]": d_to,
        "sort": "1",  # 裁判年月日降順
        "offset": offset,
    }
    return BASE + "?" + urlencode(params) + "#searched"


def parse_total(soup):
    m = re.search(r"([\d,]+)\s*件中", soup.get_text())
    return int(m.group(1).replace(",", "")) if m else 0


def split_case_number_name(line1):
    """『平成30(受)1874 請求異議事件』→ (case_number, case_name)"""
    m = re.match(r"((?:平成|令和|昭和)\d+\([^)]+\)\d+(?:等)?)\s*(.*)", line1)
    if m:
        return m.group(1), m.group(2).strip()
    return line1, ""


def field_from_case_number(case_number):
    m = CASE_NO_RE.search(case_number)
    if not m:
        return None
    code = m.group(1)
    return CODE_TO_FIELD.get(code)


def parse_date_court_line(line2):
    """2段目を分解: 裁判年月日/法廷/裁判種別/結果/原審裁判所/原審事件番号"""
    out = {"date": None, "court": None, "division": None,
           "judgeKind": None, "outcome": None,
           "genshinCourt": None, "genshinCaseNumber": None}
    # 裁判年月日（令和元年9月13日 / 令和2年3月31日 / 平成30年...）
    md = re.search(r"((?:平成|令和|昭和)(?:\d+|元)年\d+月\d+日)", line2)
    if md:
        out["date"] = md.group(1)
    if "最高裁判所" in line2:
        out["court"] = "最高裁判所"
    dv = COURT_DIV_RE.search(line2)
    if dv:
        out["division"] = dv.group(1)
    jk = JUDGE_KIND_RE.search(line2)
    if jk:
        out["judgeKind"] = jk.group(1)
    rs = RESULT_RE.search(line2)
    if rs:
        out["outcome"] = rs.group(1)
    gen = GENSHIN_RE.search(line2)
    if gen:
        out["genshinCourt"] = gen.group(1)
        out["genshinCaseNumber"] = gen.group(2)
    return out


def parse_rows(soup):
    rows = []
    for tr in soup.select("table.search-result-table tbody tr"):
        a = tr.select_one("th a")
        if not a:
            continue
        href = a.get("href", "")
        m = re.search(r"/(\d+)/detail(\d+)/", href)
        if not m:
            continue
        hanrei_id, detail_type = m.group(1), m.group(2)
        ps = tr.select("td p")
        line1 = ps[0].get_text(" ", strip=True) if len(ps) > 0 else ""
        line2 = ps[1].get_text(" ", strip=True) if len(ps) > 1 else ""
        case_number, case_name = split_case_number_name(line1)
        dc = parse_date_court_line(line2)
        pdf_a = tr.select_one("td.file-col a")
        pdf_url = None
        if pdf_a and pdf_a.get("href"):
            pdf_url = "https://www.courts.go.jp/" + pdf_a["href"].lstrip("./")
        rows.append({
            "hanreiId": hanrei_id,            # 安定ID（detailリンク/PDF名と一致）
            "detailType": detail_type,        # 最高裁は "2"
            "caseNumber": case_number,
            "caseName": case_name,
            "date": dc["date"],
            "court": dc["court"],
            "division": dc["division"],       # 大法廷/小法廷
            "judgeKind": dc["judgeKind"],     # 判決/決定
            "outcome": dc["outcome"],         # 結果
            "genshinCourt": dc["genshinCourt"],
            "genshinCaseNumber": dc["genshinCaseNumber"],
            "field": field_from_case_number(case_number),  # 符号からの一次分類
            "fullTextPdf": pdf_url,
            "detailUrl": "https://www.courts.go.jp/hanrei/" + href.lstrip("./"),
            "needsReview": False,
        })
    return rows


def crawl(g_from, y_from, m_from, d_from, g_to, y_to, m_to, d_to, sleep=1.5):
    results, offset = [], 0
    first = requests.get(
        build_url(g_from, y_from, m_from, d_from, g_to, y_to, m_to, d_to, 0),
        headers=HEADERS, timeout=30)
    first.raise_for_status()
    soup = BeautifulSoup(first.text, "html.parser")
    total = parse_total(soup)
    print(f"総件数: {total}", file=sys.stderr)
    results.extend([r for r in parse_rows(soup) if r["detailType"] == "2"])
    offset = 30
    while offset < total:
        url = build_url(g_from, y_from, m_from, d_from, g_to, y_to, m_to, d_to, offset)
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        s = BeautifulSoup(r.text, "html.parser")
        page = [x for x in parse_rows(s) if x["detailType"] == "2"]
        results.extend(page)
        print(f"offset={offset}: +{len(page)} (計{len(results)})", file=sys.stderr)
        offset += 30
        time.sleep(sleep)  # サーバー負荷配慮
    return results


if __name__ == "__main__":
    import os
    # 期間は環境変数で指定（未指定なら全期間 昭和1/1/1〜令和8/5/31）
    g_from = os.environ.get("GENGO_FROM", "昭和")
    y_from = int(os.environ.get("YEAR_FROM", "1"))
    m_from = int(os.environ.get("MONTH_FROM", "1"))
    d_from = int(os.environ.get("DAY_FROM", "1"))
    g_to = os.environ.get("GENGO_TO", "令和")
    y_to = int(os.environ.get("YEAR_TO", "8"))
    m_to = int(os.environ.get("MONTH_TO", "5"))
    d_to = int(os.environ.get("DAY_TO", "31"))
    out = os.environ.get("OUT_JSON", "opinions_list_stage1.json")
    print(f"期間: {g_from}{y_from}/{m_from}/{d_from} 〜 {g_to}{y_to}/{m_to}/{d_to}", file=sys.stderr)
    data = crawl(g_from, y_from, m_from, d_from, g_to, y_to, m_to, d_to)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"{len(data)} 件を {out} に保存しました")
