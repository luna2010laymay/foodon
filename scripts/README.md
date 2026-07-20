# 푸드온 데이터 파이프라인 스크립트

상품 데이터를 대량으로 만들기 위한 도구 모음이에요.
공공데이터(영양성분·전성분) + 상품 이미지를 합쳐 `src/products.json` 을 생성합니다.

> 실행은 **인터넷이 되는 PC**에서 하세요. (파이썬 필요)
> 설치: `pip install pillow numpy scipy requests`

## 전체 흐름
```
① 영양성분 CSV  ─┐
                 ├─▶ build_products.py ─▶ products_new.json ─▶ src/products.json 에 병합
② 전성분 API    ─┘                                   ▲
   (fetch_ingredients.py → ingredients.json)          │
③ 상품 사진 폴더 ─▶ nukki_batch.py ─▶ public/products/*.jpg ─┘
```

## 1. `fetch_ingredients.py` — 전성분(원재료) 수집
식품안전나라 '식품(첨가물)품목제조보고(원재료)' API 호출 → `ingredients.json`
```bash
# 인증키 등록 (윈도우: set / 맥·리눅스: export)
set FOOD_API_KEY=발급받은키
# 먼저 구조 확인
python scripts/fetch_ingredients.py --service 서비스ID --probe
# 전체 수집
python scripts/fetch_ingredients.py --service 서비스ID --out ingredients.json
```

## 2. `csv_nutrition.py` — 영양성분 미리보기(단건 확인용)
```bash
python scripts/csv_nutrition.py --csv 영양성분.csv --name "통밀건빵"
```

## 3. `build_products.py` — products.json 생성 (핵심)
영양성분 CSV + 전성분 JSON → 앱 형식 상품 데이터. 알레르기·카테고리 자동.
```bash
python scripts/build_products.py \
    --nutri-csv 영양성분.csv \
    --ingredients ingredients.json \
    --targets targets.txt \
    --start-id 31 --out products_new.json
```
- `targets.txt`: 포함할 품목보고번호 목록(한 줄에 하나)
- 결과 `products_new.json` 을 `src/products.json` 배열에 붙여넣으면 앱에 반영

## 4. `nukki_batch.py` — 상품 사진 누끼(배경제거)
```bash
python scripts/nukki_batch.py --indir raw --outdir public/products
```
- 파일명은 품목보고번호로 저장하면 `build_products.py` 의 `img` 경로와 자동으로 맞아요
  (예: `raw/2003044504572.jpg` → `public/products/2003044504572.jpg`)

## 자동으로 채워지는 것 / 수기 보강이 필요한 것
| 항목 | 자동 | 비고 |
|---|---|---|
| 제품명·제조사·분류·영양성분 | ✅ | 공공데이터 |
| 전성분·알레르기(contains) | ✅ | 전성분 API + 키워드 |
| 상품 이미지 | ✅(누끼) | 원본 사진은 자체몰 등에서 수집 |
| 원산지 세부 / 교차오염(같은 시설) | ✋ | 공공데이터에 없음 → 필요시 라벨 참고 수기 |
