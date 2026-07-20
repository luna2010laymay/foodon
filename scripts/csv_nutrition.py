#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
공공데이터 '통합식품영양성분정보(가공식품)' CSV → 푸드온 영양성분(nutrition) 변환기
------------------------------------------------------------------
제품명 또는 품목보고번호를 넣으면, products.json 에 그대로 넣을 수 있는
nutrition 객체(1일 기준치 % 자동 계산 포함)를 만들어 줍니다.

사용법:
  python scripts/csv_nutrition.py --csv 영양성분.csv --name "통밀건빵"
  python scripts/csv_nutrition.py --csv 영양성분.csv --bogo 1989038318734
  python scripts/csv_nutrition.py --csv 영양성분.csv --name "두유" --list   # 후보 목록만

주의: 정부 CSV는 보통 cp949 인코딩이에요(자동 처리).
------------------------------------------------------------------
"""
import argparse, csv, json, sys, re

# 한국 1일 영양성분 기준치 (라벨의 % 계산 근거) — (단위, 기준치)
DV = {
    "탄수화물": ("g", 324), "당류": ("g", 100), "식이섬유": ("g", 25),
    "단백질": ("g", 55), "지방": ("g", 54), "포화지방": ("g", 15),
    "콜레스테롤": ("mg", 300), "나트륨": ("mg", 2000),
    "칼슘": ("mg", 700), "철": ("mg", 12), "칼륨": ("mg", 3500),
}
# 표시 순서와 CSV 열 매핑 (표시명 → CSV 열명)
ORDER = [
    ("나트륨", "나트륨(mg)", "mg"),
    ("탄수화물", "탄수화물(g)", "g"),
    ("당류", "당류(g)", "g"),
    ("식이섬유", "식이섬유(g)", "g"),
    ("지방", "지방(g)", "g"),
    ("트랜스지방", "트랜스지방산(g)", "g"),
    ("포화지방", "포화지방산(g)", "g"),
    ("콜레스테롤", "콜레스테롤(mg)", "mg"),
    ("단백질", "단백질(g)", "g"),
    ("칼슘", "칼슘(mg)", "mg"),
    ("철", "철(mg)", "mg"),
]

def load(csv_path):
    for enc in ("cp949", "utf-8-sig", "utf-8"):
        try:
            with open(csv_path, encoding=enc, newline="") as f:
                return list(csv.DictReader(f))
        except UnicodeDecodeError:
            continue
    raise SystemExit("CSV 인코딩을 읽지 못했어요 (cp949/utf-8 아님).")

def num(v):
    v = (v or "").strip().replace(",", "")
    if v in ("", "해당없음", "-", "N/A"):
        return None
    try:
        return float(v)
    except ValueError:
        return None

def fmt(v):
    if v is None:
        return None
    return str(int(v)) if abs(v - round(v)) < 1e-9 else ("%g" % round(v, 2))

def pct(name, amount):
    if amount is None or name not in DV:
        return ""
    base = DV[name][1]
    return str(int(round(amount / base * 100))) + "%"

def norm_serving(s):
    s = (s or "").strip() or "100 g"
    m = re.match(r"^([\d.]+)\s*([a-zA-Z가-힣]+)$", s)  # "100g" → "100 g"
    return f"{m.group(1)} {m.group(2)}" if m else s

def make_nutrition(row):
    serving = norm_serving(row.get("영양성분함량기준량"))
    kcal = num(row.get("에너지(kcal)"))
    rows = []
    for disp, col, unit in ORDER:
        amt = num(row.get(col))
        if amt is None:
            # 나트륨·탄수·당류·지방·단백질은 0이라도 표기, 나머지는 값 없으면 생략
            if disp in ("나트륨", "탄수화물", "당류", "지방", "단백질"):
                amt = 0.0
            else:
                continue
        p = "" if disp == "트랜스지방" else pct(disp, amt)
        rows.append([disp, f"{fmt(amt)} {unit}", p])
    return {"serving": serving, "kcal": int(kcal) if kcal is not None else 0, "rows": rows}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--name", help="제품명(부분 일치)")
    ap.add_argument("--bogo", help="품목제조보고번호(정확 일치)")
    ap.add_argument("--list", action="store_true", help="후보 목록만 출력")
    args = ap.parse_args()
    if not args.name and not args.bogo:
        raise SystemExit("--name 또는 --bogo 중 하나는 필요해요.")

    data = load(args.csv)
    if args.bogo:
        hits = [r for r in data if r["품목제조보고번호"].strip() == args.bogo.strip()]
    else:
        key = args.name.strip()
        hits = [r for r in data if key in r["식품명"]]

    if not hits:
        print("매칭 결과가 없어요. (5만 건 제한 CSV라 없을 수도 있어요 → 오픈API 필요)")
        return
    if args.list or len(hits) > 1:
        print(f"후보 {len(hits)}개:")
        for r in hits[:20]:
            print(f"  [{r['품목제조보고번호']}] {r['식품명']} · {r['제조사명']} · {r['에너지(kcal)']}kcal")
        if args.list:
            return
        print("\n→ 가장 위 항목으로 변환합니다. (정확히 고르려면 --bogo 사용)\n")

    r = hits[0]
    nut = make_nutrition(r)
    print(f"// {r['식품명']} · {r['제조사명']} · 품목보고번호 {r['품목제조보고번호']}")
    print("nutrition: " + json.dumps(nut, ensure_ascii=False, indent=None)
          .replace('"serving"', "serving").replace('"kcal"', "kcal").replace('"rows"', "rows"))

if __name__ == "__main__":
    main()
