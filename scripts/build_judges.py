#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
judges.json 生成スクリプト（最高裁 現職裁判官）
- 一覧ページ https://www.courts.go.jp/saikosai/about/saibankan/index.html から
  現職15名（長官1＋判事14）の 氏名/所属小法廷/個別ページURL を取得
- 各個別ページから 読み仮名/生年/略歴(学歴・職歴)/任官日 を取得
- judgeId は個別ページURLのスラッグ（例 imasaki, miura）を採用＝安定IDになる
※ courts.go.jp 接続が必要。手元PCかGitHub Actionsで実行。
   実行前: pip install requests beautifulsoup4
"""

import requests, re, json, time, sys
from bs4 import BeautifulSoup
from urllib.parse import urljoin

LIST_URL = "https://www.courts.go.jp/saikosai/about/saibankan/index.html"
HEADERS = {"User-Agent": "Mozilla/5.0 (SupremeCourtWatch research bot; contact: example@example.com)"}

GENGO = {"昭和": 1925, "平成": 1988, "令和": 2018}  # 元年=+1年（昭和元年=1926 等）


def to_seireki(gengo, year):
    """元号+年 → 西暦。元年は year=1扱い。"""
    base = GENGO.get(gengo)
    if base is None:
        return None
    return base + int(year)


def parse_birth(text):
    """『(昭和32年11月10日生)』→ {'gengo':'昭和','year':32,'seireki':1957,'raw':...}"""
    m = re.search(r"(昭和|平成|令和)(\d+|元)年(\d+)月(\d+)日生", text)
    if not m:
        return None
    g = m.group(1)
    y = 1 if m.group(2) == "元" else int(m.group(2))
    return {
        "gengo": g, "year": y, "month": int(m.group(3)), "day": int(m.group(4)),
        "seireki": to_seireki(g, y), "raw": m.group(0).strip("()"),
    }


def parse_judge_page(url):
    """個別ページから 読み/生年/略歴 を取得"""
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    r.encoding = r.apparent_encoding  # 文字コードを正しく判定（文字化け対策）
    soup = BeautifulSoup(r.text, "html.parser")
    text = soup.get_text("\n", strip=True)

    # 読み仮名: 「今崎幸彦(いまさきゆきひこ)」
    reading = None
    mr = re.search(r"[一-龥々\s]+[(（]([ぁ-んー]+)[)）]", text)
    if mr:
        reading = mr.group(1)

    birth = parse_birth(text)

    # 略歴: 「略歴」見出し以降、「信条」or「最高裁において関与」までを行で取得
    career = []
    appointed_judge = None  # 判事補/判事 任官
    mcar = re.search(r"略歴\n(.+?)(?:信条|最高裁において関与|※)", text, re.S)
    if mcar:
        lines = [l.strip() for l in mcar.group(1).split("\n") if l.strip()]
        # 「平成 7年 / 判事 …」のように 年→内容 が交互に来る形を結合
        i = 0
        while i < len(lines):
            ym = re.match(r"(昭和|平成|令和)\s*(\d+|元)年(\d+月\d+日)?$", lines[i])
            if ym and i + 1 < len(lines):
                career.append({"date": lines[i], "event": lines[i + 1]})
                i += 2
            else:
                # 年が付かない補足行（前項に付随）
                if career:
                    career[-1]["event"] += " " + lines[i]
                i += 1

    return {"reading": reading, "birth": birth, "career": career}


def crawl_judges(fetch_detail=True, sleep=1.5):
    r = requests.get(LIST_URL, headers=HEADERS, timeout=30)
    r.raise_for_status()
    r.encoding = r.apparent_encoding  # 文字コードを正しく判定（文字化け対策）
    soup = BeautifulSoup(r.text, "html.parser")

    judges = []
    # 実構造: <h3>役職</h3> の後に <dl><dt><a href="./{slug}/index.html">氏名</a></dt><dd>小法廷</dd></dl>
    # h3とdlを文書順にたどり、直近のh3で役職を判定する
    role = None
    for el in soup.find_all(["h3", "dl"]):
        if el.name == "h3":
            t = el.get_text(strip=True)
            if "長官" in t:
                role = "長官"
            elif "判事" in t:
                role = "判事"
            continue
        # el is <dl>
        a = el.select_one("dt a")
        if not a:
            continue
        href = a.get("href", "")
        m = re.search(r"\./?([^/]+)/index\.html$", href)
        if not m:
            continue
        slug = m.group(1)
        if slug in ("hanzi_itiran",):  # 一覧表リンクは除外
            continue
        name = a.get_text(strip=True)
        dd = el.select_one("dd")
        court = None
        if dd:
            cm = re.search(r"(大法廷|第[一二三]小法廷)", dd.get_text())
            court = cm.group(1) if cm else None
        judges.append({
            "judgeId": slug,
            "name": name,
            "nameNormalized": name.replace(" ", "").replace("　", ""),
            "role": role,
            "division": court,
            "status": "現職",
            "detailUrl": urljoin(LIST_URL, href),
            "reading": None, "birth": None, "career": [],
        })

    if fetch_detail:
        for j in judges:
            try:
                d = parse_judge_page(j["detailUrl"])
                j.update(d)
            except Exception as e:
                print(f"  詳細取得失敗 {j['name']}: {e}", file=sys.stderr)
            time.sleep(sleep)

    return judges


if __name__ == "__main__":
    fetch = "--no-detail" not in sys.argv
    data = crawl_judges(fetch_detail=fetch)
    with open("judges.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"{len(data)} 名を judges.json に保存")
