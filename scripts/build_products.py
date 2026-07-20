#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
푸드온 products.json 자동 생성기
------------------------------------------------------------------
영양성분(공공데이터 CSV) + 전성분(원재료 API 결과 JSON) 을 합쳐,
앱에 바로 넣을 수 있는 products.json 항목을 만들어 줍니다.

  · 영양성분 → CSV 에서 자동 (품목보고번호 매칭)
  · 카테고리 → 식품분류 → 앱 카테고리 자동 매핑
  · 알레르기(contains) → 전성분에서 자동 추출
  · 전성분 라벨(allergy/additive) → 키워드로 자동 태깅
  · 이미지 → /products/{품목보고번호}.jpg 경로 (별도로 누끼해서 채움)

사용법:
  python scripts/build_products.py \
      --nutri-csv 영양성분.csv \
      --ingredients ingredients.json \
      --targets targets.txt \
      --start-id 31 \
      --out products_new.json

  · targets.txt : 한 줄에 품목보고번호 하나 (전성분 JSON 의 키와 동일)
  · ingredients.json : { "품목보고번호": "밀가루(밀:국산),현미가루,설탕,...", ... }
      (원재료 API fetch 결과. fetch_ingredients.py 로 생성)
------------------------------------------------------------------
"""
import argparse, csv, json, re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from csv_nutrition import load as load_csv, make_nutrition  # 영양성분 재사용

# ---- 식품 대분류 → 앱 카테고리 (+ 대체 이모지) ----
CAT_MAP = {
    "음료류": ("음료", "🥤"),
    "다류": ("음료", "🍵"),
    "과자류·빵류 또는 떡류": ("과자", "🍪"),
    "코코아가공품류 또는 초콜릿류": ("초콜릿", "🍫"),
    "면류": ("면류", "🍜"),
    "즉석식품류": ("간편식", "🍱"),
    "두부류 또는 묵류": ("두부·묵", "🧈"),
    "유가공품류": ("유제품", "🥛"),
    "식육가공품 및 포장육": ("축산·델리", "🥓"),
    "알가공품류": ("축산·델리", "🥚"),
    "동물성가공식품류": ("축산·델리", "🍖"),
    "수산가공식품류": ("수산가공", "🐟"),
    "농산가공식품류": ("농산가공", "🌾"),
    "당류": ("당류", "🍬"),
    "조미식품": ("조미", "🧂"),
    "식용유지류": ("유지", "🫙"),
    "빙과류": ("빙과", "🍦"),
    "벌꿀 및 화분가공 식품류": ("기타", "🍯"),
    "기타식품류": ("기타", "📦"),
}
def map_cat(daebun):
    return CAT_MAP.get((daebun or "").strip(), ("기타", "📦"))

# ---- 알레르기(한국 표시대상) 동의어 → 대표명 ----
ALLERGEN = {
    "우유": ["우유", "유청", "유장", "분유", "치즈", "버터", "연유", "유크림", "카제인", "탈지분유", "가공유"],
    "대두": ["대두", "두유", "된장", "간장(대두", "분리대두"],
    "밀": ["밀", "소맥", "글루텐"],
    "계란": ["계란", "달걀", "난백", "난황", "전란", "난분", "알류"],
    "땅콩": ["땅콩", "낙화생"],
    "호두": ["호두"], "잣": ["잣"], "메밀": ["메밀"], "복숭아": ["복숭아"], "토마토": ["토마토"],
    "새우": ["새우"], "게": ["게살", "게다리", "꽃게", "대게", "홍게", "게(",],
    "돼지고기": ["돼지고기", "돈육"], "쇠고기": ["쇠고기", "소고기", "우육"], "닭고기": ["닭고기", "계육"],
    "고등어": ["고등어"], "오징어": ["오징어"], "조개류": ["조개", "굴", "전복", "홍합", "바지락"],
    "아황산류": ["아황산", "메타중아황산"],
}
# ---- 첨가물 판단 키워드 ----
ADDITIVE_KW = ["제제", "색소", "향료", "감미료", "보존료", "산도조절제", "유화제", "증점제",
    "안정제", "팽창제", "발색제", "표백제", "산화방지제", "글루타민산나트륨", "l-글루타민산",
    "스테비아", "수크랄로스", "아스파탐", "아세설팜", "사카린", "카라기난", "잔탄검", "구아검",
    "젤란검", "펙틴", "구연산", "젖산", "사과산", "인산", "탄산수소나트륨", "탄산칼슘", "덱스트린",
    "말토덱스트린", "정제염", "효소", "프로테아제", "토코페롤", "이산화규소", "합성", "이나트륨",
    "올리고당", "아라비아검"]

def label_ing(name):
    """성분명 → 라벨 배열 (allergy / additive)."""
    labels = []
    low = name
    if any(any(sy in low for sy in syns) for syns in ALLERGEN.values()):
        labels.append("allergy")
    if any(kw in low.lower() for kw in ADDITIVE_KW):
        labels.append("additive")
    return labels

def find_contains(raw):
    """전성분 전체 문자열 → 포함 알레르기 대표명 목록."""
    found = []
    for rep, syns in ALLERGEN.items():
        if any(sy in raw for sy in syns):
            found.append(rep)
    return found

def split_ingredients(raw):
    """전성분 문자열을 최상위 콤마로 분리 (괄호·대괄호 안의 콤마는 무시)."""
    out, depth, cur = [], 0, ""
    for ch in raw:
        if ch in "([{": depth += 1
        elif ch in ")]}": depth = max(0, depth - 1)
        if ch == "," and depth == 0:
            if cur.strip(): out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip(): out.append(cur.strip())
    return out

def build_ing(raw):
    """전성분 원문 → [[성분명,[라벨]], ...]"""
    items = split_ingredients(raw)
    return [[it, label_ing(it)] for it in items]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nutri-csv", required=True)
    ap.add_argument("--ingredients", help="원재료 API 결과 JSON {품목보고번호: 전성분문자열}")
    ap.add_argument("--targets", help="포함할 품목보고번호 목록 파일(한 줄에 하나). 없으면 ingredients 의 키 전체")
    ap.add_argument("--start-id", type=int, default=31)
    ap.add_argument("--out", default="products_new.json")
    args = ap.parse_args()

    rows = load_csv(args.nutri_csv)
    by_bogo = {}
    for r in rows:
        by_bogo.setdefault(r["품목제조보고번호"].strip(), r)

    ing_map = {}
    if args.ingredients and os.path.exists(args.ingredients):
        ing_map = json.load(open(args.ingredients, encoding="utf-8"))

    if args.targets and os.path.exists(args.targets):
        targets = [l.strip() for l in open(args.targets, encoding="utf-8") if l.strip()]
    else:
        targets = list(ing_map.keys())

    products, pid, missing = [], args.start_id, []
    for bogo in targets:
        row = by_bogo.get(bogo)
        if not row:
            missing.append(bogo); continue
        cat, emoji = map_cat(row["식품대분류명"])
        raw_ing = ing_map.get(bogo, "").strip()
        p = {
            "id": pid,
            "name": row["식품명"].strip(),
            "brand": (row["제조사명"] or row.get("유통업체명", "")).strip(),
            "cat": cat, "emoji": emoji,
            "img": f"/products/{bogo}.jpg",
        }
        if raw_ing:
            p["ing"] = build_ing(raw_ing)
            contains = find_contains(raw_ing)
            if contains: p["contains"] = contains
        else:
            p["ing"] = []   # 전성분 미확보 → 나중에 채움
        p["facility"] = []  # 교차오염(같은 시설)은 공공데이터에 없음 → 필요시 수기
        p["nutrition"] = make_nutrition(row)
        p["reviews"] = []
        products.append(p); pid += 1

    json.dump(products, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"생성: {len(products)}개 → {args.out}")
    if missing:
        print(f"CSV에 없는 품목보고번호 {len(missing)}개 (5만 제한 CSV라 그럴 수 있음): {missing[:5]}...")
    # 전성분 없는 항목 경고
    no_ing = [p['name'] for p in products if not p['ing']]
    if no_ing:
        print(f"전성분 미확보 {len(no_ing)}개(이미지·전성분 보강 필요): {no_ing[:5]}")

if __name__ == "__main__":
    main()
