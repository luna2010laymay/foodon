#!/usr/bin/env python3
"""배추 시세 예측용 5년치 샘플 데이터 생성기.

실제 API 키(KAMIS·기상청·KOSIS)가 없는 환경에서도 예측 파이프라인을
바로 돌려볼 수 있도록, 실제 통계 패턴(가락시장 배추 도매가 계절성,
서울/강원 기상 평년값, 배추 작형별 재배면적)을 본떠 만든 **합성 데이터**를
data/ 폴더에 CSV로 저장한다.

⚠️ 이 데이터는 실측치가 아님. 실측 데이터는 fetch_data.py 로 수집해서
   같은 파일명으로 덮어쓰면 predict.py 가 그대로 사용한다.

생성 파일 (모두 월 단위):
  data/price_garak.csv    : date, price      — 가락시장 배추 상품 도매가 (원/10kg망)
  data/weather.csv        : date, tavg, rain, hot_days, cold_days
  data/area.csv           : year, spring_ha, highland_ha, autumn_ha — 작형별 재배면적(ha)
"""
import csv
import math
import os
import random

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")

START_YEAR, END_YEAR = 2021, 2025  # 최근 5년

# 월별 평년 기상 (서울/강원 혼합 기준 대략치): (평균기온℃, 강수량mm)
CLIMATE_NORM = {
    1: (-2.0, 20), 2: (0.5, 25), 3: (6.0, 45), 4: (12.5, 75),
    5: (18.0, 100), 6: (22.5, 130), 7: (25.5, 400), 8: (26.0, 350),
    9: (21.5, 140), 10: (14.5, 55), 11: (7.0, 50), 12: (0.0, 25),
}

# 배추 도매가 월별 계절 계수 (겨울 김장 후 저가 ~ 여름·초가을 고랭지기 고가)
SEASON_FACTOR = {
    1: 0.80, 2: 0.85, 3: 0.95, 4: 1.00, 5: 0.90, 6: 0.95,
    7: 1.15, 8: 1.45, 9: 1.55, 10: 1.10, 11: 0.85, 12: 0.75,
}

BASE_PRICE = 8000  # 원/10kg망 기준가

# 연도별 재배면적(ha) — 감소 추세 반영한 대략치
AREA = {
    2021: (13500, 5300, 13800),
    2022: (13100, 5100, 13300),
    2023: (12800, 4900, 13100),
    2024: (12300, 4700, 12600),
    2025: (12000, 4600, 12200),
}


def month_range():
    for y in range(START_YEAR, END_YEAR + 1):
        for m in range(1, 13):
            yield y, m


def main():
    os.makedirs(DATA, exist_ok=True)
    rng = random.Random(42)

    # 1) 기상: 평년값 + 연도별 이상기후 (2022·2024 여름 폭염 강화)
    weather = {}
    for y, m in month_range():
        tnorm, rnorm = CLIMATE_NORM[m]
        t_anom = rng.gauss(0, 1.0)
        r_mult = max(0.2, rng.gauss(1.0, 0.35))
        if m in (7, 8) and y in (2022, 2024):   # 폭염 해
            t_anom += 1.8
        if m in (8, 9) and y in (2022, 2024):   # 태풍·집중호우 해
            r_mult *= 1.6
        tavg = round(tnorm + t_anom, 1)
        rain = round(rnorm * r_mult, 1)
        hot = max(0, round((tavg - 24) * 3)) if m in (6, 7, 8, 9) else 0
        cold = max(0, round((-2 - tavg) * 3)) if m in (12, 1, 2) else 0
        weather[(y, m)] = (tavg, rain, hot, cold)

    # 2) 가격: 계절성 × 기상충격(1~2개월 지연) × 재배면적 효과 + 관성 + 노이즈
    prices = {}
    prev_shock = 0.0
    for y, m in month_range():
        # 생육기(1~2개월 전) 기상 충격: 폭염일수·강수 과다 → 공급 감소 → 가격 상승
        shock = 0.0
        for lag in (1, 2):
            ly, lm = (y, m - lag) if m > lag else (y - 1, m - lag + 12)
            if (ly, lm) in weather:
                tavg, rain, hot, _ = weather[(ly, lm)]
                shock += hot * 0.012
                rnorm = CLIMATE_NORM[lm][1]
                if rain > rnorm * 1.5:
                    shock += 0.10
        # 재배면적: 해당 월 출하 작형 면적이 평균 대비 적으면 가격 상승
        spring, highland, autumn = AREA.get(y, AREA[END_YEAR])
        if m in (7, 8, 9, 10):
            area_now, area_base = highland, 5000
        elif m in (5, 6):
            area_now, area_base = spring, 12800
        else:
            area_now, area_base = autumn, 13000
        area_factor = (area_base / area_now) ** 1.5

        shock = 0.6 * prev_shock + shock  # 충격은 서서히 해소
        prev_shock = shock
        price = BASE_PRICE * SEASON_FACTOR[m] * area_factor * (1 + shock)
        price *= max(0.75, rng.gauss(1.0, 0.08))
        prices[(y, m)] = int(round(price, -1))

    # 3) 저장
    with open(os.path.join(DATA, "price_garak.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "price"])
        for (y, m), p in prices.items():
            w.writerow([f"{y}-{m:02d}", p])

    with open(os.path.join(DATA, "weather.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "tavg", "rain", "hot_days", "cold_days"])
        for (y, m), (t, r, h, c) in weather.items():
            w.writerow([f"{y}-{m:02d}", t, r, h, c])

    with open(os.path.join(DATA, "area.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["year", "spring_ha", "highland_ha", "autumn_ha"])
        for y, (s, hl, a) in AREA.items():
            w.writerow([y, s, hl, a])

    print(f"샘플 데이터 생성 완료 → {DATA}/ (price_garak.csv, weather.csv, area.csv)")
    print(f"기간: {START_YEAR}-01 ~ {END_YEAR}-12 ({len(prices)}개월)")


if __name__ == "__main__":
    main()
