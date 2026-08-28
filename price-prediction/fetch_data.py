#!/usr/bin/env python3
"""실측 데이터 수집기 — API 키가 있을 때 사용.

환경변수에 키를 넣고 실행하면 data/ 에 실측 CSV를 저장한다
(predict.py 는 이 파일들을 그대로 읽음. 키가 없으면 generate_sample_data.py 의
샘플 데이터로 대체 가능).

필요 환경변수:
  KAMIS_CERT_KEY / KAMIS_CERT_ID : KAMIS 오픈API (www.kamis.or.kr) — 가락시장 포함 서울 도매가
  KMA_API_KEY                    : 기상청 API허브 (apihub.kma.go.kr) — 지상관측 월값
  KOSIS_API_KEY                  : KOSIS 공유서비스 (kosis.kr) — 배추 재배면적

사용:
  python3 fetch_data.py --start 2021-01 --end 2025-12

⚠️ API 키는 절대 코드/커밋에 넣지 말 것 (환경변수로만).
"""
import argparse
import csv
import json
import os
import sys
import urllib.parse
import urllib.request
from collections import defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")

# KAMIS 품목코드: 배추(200류/211), 도매, 상품, 서울(가락시장 반영)
KAMIS_URL = "https://www.kamis.or.kr/service/price/xml.do"
KMA_URL = "https://apihub.kma.go.kr/api/typ01/url/sts_mon.php"  # 월 통계
KOSIS_URL = "https://kosis.kr/openapi/Param/statisticsParameterData.do"


def http_json(url, params):
    q = urllib.parse.urlencode(params)
    with urllib.request.urlopen(f"{url}?{q}", timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_kamis_price(start, end):
    """월별 배추 도매가(원/10kg) — KAMIS periodProductList를 연 단위로 나눠 호출."""
    key, cid = os.environ.get("KAMIS_CERT_KEY"), os.environ.get("KAMIS_CERT_ID")
    if not key or not cid:
        print("  [건너뜀] KAMIS_CERT_KEY / KAMIS_CERT_ID 없음")
        return None
    monthly = defaultdict(list)
    sy, ey = int(start[:4]), int(end[:4])
    for y in range(sy, ey + 1):
        data = http_json(KAMIS_URL, {
            "action": "periodProductList", "p_productclscode": "02",  # 도매
            "p_startday": f"{y}-01-01", "p_endday": f"{y}-12-31",
            "p_itemcategorycode": "200", "p_itemcode": "211",  # 배추
            "p_kindcode": "00", "p_productrankcode": "04",  # 상품
            "p_countrycode": "1101",  # 서울 (가락시장 시세 반영)
            "p_convert_kg_yn": "N",
            "p_cert_key": key, "p_cert_id": cid, "p_returntype": "json",
        })
        items = data.get("data", {}).get("item", [])
        for it in items:
            ym = f"{it.get('yyyy', y)}-{str(it.get('regday', '01/01')).split('/')[0].zfill(2)}"
            p = str(it.get("price", "")).replace(",", "")
            if p.replace(".", "").isdigit():
                monthly[ym].append(float(p))
    if not monthly:
        return None
    rows = [(ym, round(sum(v) / len(v))) for ym, v in sorted(monthly.items())
            if start <= ym <= end]
    return rows


def fetch_kma_weather(start, end):
    """월별 평균기온·강수량·폭염/한파일수 — 기상청 API허브 (서울 108 지점)."""
    key = os.environ.get("KMA_API_KEY")
    if not key:
        print("  [건너뜀] KMA_API_KEY 없음")
        return None
    q = urllib.parse.urlencode({
        "tm1": start.replace("-", "") + "01", "tm2": end.replace("-", "") + "31",
        "stn": "108", "authKey": key,
    })
    with urllib.request.urlopen(f"{KMA_URL}?{q}", timeout=60) as r:
        text = r.read().decode("euc-kr", errors="replace")
    rows = []
    for line in text.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        f = line.split()
        # sts_mon 포맷: TM(YYYYMM) STN ... TA_AVG ... RN_SUM ... (컬럼 위치는 헤더 주석 참고)
        try:
            ym = f"{f[0][:4]}-{f[0][4:6]}"
            rows.append((ym, float(f[10]), float(f[39]), 0, 0))
        except (IndexError, ValueError):
            continue
    return rows or None


def fetch_kosis_area(start, end):
    """연도별 배추 재배면적(ha) — KOSIS 농작물생산조사."""
    key = os.environ.get("KOSIS_API_KEY")
    if not key:
        print("  [건너뜀] KOSIS_API_KEY 없음")
        return None
    data = http_json(KOSIS_URL, {
        "method": "getList", "apiKey": key, "format": "json", "jsonVD": "Y",
        "orgId": "101", "tblId": "DT_1ET0027",  # 농작물생산조사(배추)
        "objL1": "ALL", "itmId": "T001",
        "prdSe": "Y", "startPrdDe": start[:4], "endPrdDe": end[:4],
    })
    if not isinstance(data, list):
        return None
    by_year = defaultdict(dict)
    for it in data:
        by_year[it.get("PRD_DE")][it.get("C1_NM", "")] = it.get("DT")
    rows = []
    for y, d in sorted(by_year.items()):
        try:
            rows.append((int(y), float(d.get("봄배추", 0)),
                         float(d.get("고랭지배추", 0)), float(d.get("가을배추", 0))))
        except (TypeError, ValueError):
            continue
    return rows or None


def save(path, header, rows):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"  저장: {path} ({len(rows)}행)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2021-01")
    ap.add_argument("--end", default="2025-12")
    a = ap.parse_args()
    os.makedirs(DATA, exist_ok=True)
    ok = False

    print("1) KAMIS 가락시장(서울) 배추 도매가 수집…")
    rows = fetch_kamis_price(a.start, a.end)
    if rows:
        save(os.path.join(DATA, "price_garak.csv"), ["date", "price"], rows)
        ok = True

    print("2) 기상청 월별 기상 수집…")
    rows = fetch_kma_weather(a.start, a.end)
    if rows:
        save(os.path.join(DATA, "weather.csv"),
             ["date", "tavg", "rain", "hot_days", "cold_days"], rows)
        ok = True

    print("3) KOSIS 배추 재배면적 수집…")
    rows = fetch_kosis_area(a.start, a.end)
    if rows:
        save(os.path.join(DATA, "area.csv"),
             ["year", "spring_ha", "highland_ha", "autumn_ha"], rows)
        ok = True

    if not ok:
        print("\n수집된 데이터가 없어요. API 키를 설정하거나, "
              "python3 generate_sample_data.py 로 샘플 데이터를 만들어 주세요.")
        sys.exit(1)


if __name__ == "__main__":
    main()
