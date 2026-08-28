#!/usr/bin/env python3
"""배추(가락시장) 단가 예측 프로그램.

최근 5년 월별 데이터(기상·가락시장 도매단가·재배면적)로 그래디언트부스팅
모델을 학습해 다음 달 이후 단가를 예측한다.

예측 인자(피처):
  · 3개월 전 단가 (price_lag_3m)        ← 요청 인자
  · 작년 동월(동기간) 단가 (price_lag_12m) ← 요청 인자
  · 1개월 전 단가 (가격 관성)
  · 생육기(1~2개월 전) 기상: 평균기온 편차·강수량 비율·폭염일수
  · 해당 월 출하 작형의 재배면적 (봄/고랭지/가을배추)
  · 월 계절성 (sin/cos)

사용:
  python3 predict.py                 # 학습 + 성능평가 + 6개월 예측
  python3 predict.py --horizon 3     # 3개월 예측
데이터는 data/*.csv (없으면 generate_sample_data.py 먼저 실행).
"""
import argparse
import math
import os
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")

# 월별 평년 기상 (generate_sample_data.py 와 동일 기준: 기온℃, 강수mm)
CLIMATE_NORM = {
    1: (-2.0, 20), 2: (0.5, 25), 3: (6.0, 45), 4: (12.5, 75),
    5: (18.0, 100), 6: (22.5, 130), 7: (25.5, 400), 8: (26.0, 350),
    9: (21.5, 140), 10: (14.5, 55), 11: (7.0, 50), 12: (0.0, 25),
}

FEATURES = [
    "price_lag_3m", "price_lag_12m", "price_lag_1m",
    "tavg_anom_lag1", "rain_ratio_lag1", "hot_days_lag1",
    "tavg_anom_lag2", "rain_ratio_lag2", "hot_days_lag2",
    "area_ha", "month_sin", "month_cos",
]
FEATURE_KO = {
    "price_lag_3m": "3개월 전 단가", "price_lag_12m": "작년 동월 단가",
    "price_lag_1m": "1개월 전 단가",
    "tavg_anom_lag1": "1개월 전 기온편차", "rain_ratio_lag1": "1개월 전 강수비율",
    "hot_days_lag1": "1개월 전 폭염일수",
    "tavg_anom_lag2": "2개월 전 기온편차", "rain_ratio_lag2": "2개월 전 강수비율",
    "hot_days_lag2": "2개월 전 폭염일수",
    "area_ha": "출하작형 재배면적", "month_sin": "계절성(sin)", "month_cos": "계절성(cos)",
}


def load_data():
    need = ["price_garak.csv", "weather.csv", "area.csv"]
    missing = [f for f in need if not os.path.exists(os.path.join(DATA, f))]
    if missing:
        sys.exit(f"데이터 파일이 없어요: {missing}\n"
                 f"→ 실측: python3 fetch_data.py  /  샘플: python3 generate_sample_data.py")
    price = pd.read_csv(os.path.join(DATA, "price_garak.csv"))
    weather = pd.read_csv(os.path.join(DATA, "weather.csv"))
    area = pd.read_csv(os.path.join(DATA, "area.csv"))
    df = price.merge(weather, on="date", how="left")
    df["date"] = pd.PeriodIndex(df["date"], freq="M")
    df = df.sort_values("date").reset_index(drop=True)
    return df, area.set_index("year")


def area_for_month(area, year, month):
    """해당 월에 주로 출하되는 작형의 재배면적(ha)."""
    y = year if year in area.index else area.index.max()
    row = area.loc[y]
    if month in (7, 8, 9, 10):
        return row["highland_ha"]   # 고랭지배추
    if month in (5, 6):
        return row["spring_ha"]     # 봄배추
    return row["autumn_ha"]         # 가을·월동배추


def build_features(df, area):
    d = df.copy()
    d["price_lag_1m"] = d["price"].shift(1)
    d["price_lag_3m"] = d["price"].shift(3)     # ← 3개월 전 단가
    d["price_lag_12m"] = d["price"].shift(12)   # ← 작년 동기간 단가
    for lag in (1, 2):
        t = d["tavg"].shift(lag)
        r = d["rain"].shift(lag)
        lag_month = [p.month for p in (d["date"] - lag)]
        tnorm = np.array([CLIMATE_NORM[mm][0] for mm in lag_month])
        rnorm = np.array([CLIMATE_NORM[mm][1] for mm in lag_month])
        d[f"tavg_anom_lag{lag}"] = t.to_numpy() - tnorm
        d[f"rain_ratio_lag{lag}"] = r.to_numpy() / rnorm
        d[f"hot_days_lag{lag}"] = d["hot_days"].shift(lag)
    d["area_ha"] = [area_for_month(area, p.year, p.month) for p in d["date"]]
    d["month_sin"] = np.sin(2 * np.pi * d["date"].dt.month / 12)
    d["month_cos"] = np.cos(2 * np.pi * d["date"].dt.month / 12)
    return d.dropna(subset=FEATURES + ["price"]).reset_index(drop=True)


def make_model():
    return GradientBoostingRegressor(
        n_estimators=300, learning_rate=0.05, max_depth=3,
        subsample=0.9, random_state=42)


def walk_forward_eval(d, n_test=12):
    """마지막 n_test개월을 한 달씩 전진 검증 (미래 정보 누출 없음)."""
    preds, actuals, dates = [], [], []
    for i in range(len(d) - n_test, len(d)):
        train, test = d.iloc[:i], d.iloc[i]
        model = make_model()
        model.fit(train[FEATURES], train["price"])
        preds.append(float(model.predict(test[FEATURES].to_frame().T)[0]))
        actuals.append(float(test["price"]))
        dates.append(str(test["date"]))
    preds, actuals = np.array(preds), np.array(actuals)
    mae = mean_absolute_error(actuals, preds)
    mape = float(np.mean(np.abs((actuals - preds) / actuals)) * 100)
    # 비교 기준: 작년 동월 단가를 그대로 쓰는 나이브 예측
    naive = d.iloc[len(d) - n_test:]["price_lag_12m"].to_numpy()
    naive_mape = float(np.mean(np.abs((actuals - naive) / actuals)) * 100)
    return dates, preds, actuals, mae, mape, naive_mape


def forecast(d, df_raw, area, horizon):
    """다음 horizon개월 재귀 예측 (예측한 단가를 다음 달 lag 피처로 재사용).
    미래 기상은 평년값, 재배면적은 최근 연도 값으로 가정."""
    model = make_model()
    model.fit(d[FEATURES], d["price"])

    hist = {str(p): v for p, v in zip(df_raw["date"], df_raw["price"])}
    last = df_raw["date"].iloc[-1]
    out = []
    for step in range(1, horizon + 1):
        cur = last + step
        y, m = cur.year, cur.month

        def get_price(period):
            return hist.get(str(period))

        row = {
            "price_lag_1m": get_price(cur - 1),
            "price_lag_3m": get_price(cur - 3),
            "price_lag_12m": get_price(cur - 12),
            "area_ha": area_for_month(area, y, m),
            "month_sin": math.sin(2 * math.pi * m / 12),
            "month_cos": math.cos(2 * math.pi * m / 12),
        }
        for lag in (1, 2):
            lm = (cur - lag).month
            row[f"tavg_anom_lag{lag}"] = 0.0            # 평년 가정
            row[f"rain_ratio_lag{lag}"] = 1.0
            row[f"hot_days_lag{lag}"] = 6.0 if lm in (7, 8) else 0.0
        if any(row[k] is None for k in ("price_lag_1m", "price_lag_3m", "price_lag_12m")):
            break
        x = pd.DataFrame([row])[FEATURES]
        p = float(model.predict(x)[0])
        hist[str(cur)] = p
        out.append((str(cur), int(round(p, -1))))
    return model, out


def main():
    ap = argparse.ArgumentParser(description="배추 가락시장 단가 예측")
    ap.add_argument("--horizon", type=int, default=6, help="예측 개월 수 (기본 6)")
    a = ap.parse_args()

    df, area = load_data()
    d = build_features(df, area)
    print("🥬 배추(가락시장) 단가 예측 프로그램")
    print(f"  데이터: {df['date'].iloc[0]} ~ {df['date'].iloc[-1]} "
          f"({len(df)}개월, 학습가능 {len(d)}개월)")

    # 1) 전진 검증
    n_test = min(12, max(4, len(d) // 4))
    dates, preds, actuals, mae, mape, naive_mape = walk_forward_eval(d, n_test)
    print(f"\n[검증] 최근 {n_test}개월 전진(walk-forward) 검증")
    print(f"  MAE  : {mae:,.0f}원/10kg")
    print(f"  MAPE : {mape:.1f}%  (나이브 '작년 동월 단가' 예측: {naive_mape:.1f}%)")
    print(f"  {'월':<9}{'실제':>10}{'예측':>10}{'오차':>9}")
    for dt, act, pr in zip(dates, actuals, preds):
        print(f"  {dt:<9}{act:>10,.0f}{pr:>10,.0f}{pr-act:>+9,.0f}")

    # 2) 인자 중요도
    full = make_model().fit(d[FEATURES], d["price"])
    imp = sorted(zip(FEATURES, full.feature_importances_), key=lambda x: -x[1])
    print("\n[인자 중요도] (모델이 예측에 활용한 비중)")
    for name, v in imp:
        mark = " ★" if name in ("price_lag_3m", "price_lag_12m") else ""
        print(f"  {FEATURE_KO[name]:<14}{v*100:5.1f}%{mark}")

    # 3) 미래 예측
    _, fc = forecast(d, df, area, a.horizon)
    print(f"\n[예측] 향후 {len(fc)}개월 가락시장 배추 도매가 (원/10kg망)")
    for ym, p in fc:
        print(f"  {ym} : {p:,}원")
    out_csv = os.path.join(DATA, "forecast.csv")
    pd.DataFrame(fc, columns=["date", "predicted_price"]).to_csv(out_csv, index=False)
    print(f"\n예측 결과 저장 → {out_csv}")
    print("※ 미래 기상은 평년값 가정. 샘플 데이터 사용 시 결과는 데모용이에요.")


if __name__ == "__main__":
    main()
