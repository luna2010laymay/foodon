# 푸드온 데이터 파이프라인 스크립트

공공데이터(영양성분·전성분) + 상품 이미지를 합쳐 `src/products.json` 을 대량 생성합니다.

> 실행은 **인터넷 되는 PC**에서. 준비: `pip install pillow numpy scipy requests`

## 준비물
- `영양성분.csv` — 공공데이터포털 '전국통합식품영양성분정보(가공식품)' CSV
- 전성분 API 인증키 (식품안전나라, 서비스 C002)

## 4단계 실행
```bash
# 1) 대상 상품의 품목보고번호 목록 만들기 (예: 풀무원)
python scripts/make_targets.py --csv 영양성분.csv --brand 풀무원 --out targets.txt

# 2) 전성분 수집  (인증키 등록: 윈도우 set / 맥 export)
set FOOD_API_KEY=발급받은키
python scripts/fetch_ingredients.py --targets targets.txt --out ingredients.json
#   (연결확인만: python scripts/fetch_ingredients.py --probe)

# 3) products.json 생성 (영양성분 + 전성분 → 앱 형식, 알레르기/카테고리 자동)
python scripts/build_products.py --nutri-csv 영양성분.csv \
    --ingredients ingredients.json --targets targets.txt \
    --start-id 31 --out products_new.json

# 4) 상품 사진 누끼 (raw/ 폴더에 원본 사진, 파일명=품목보고번호.jpg)
python scripts/nukki_batch.py --indir raw --outdir public/products
```
→ 마지막에 `products_new.json` 내용을 `src/products.json` 배열에 붙여넣으면 앱에 반영.

## 스크립트별 요약
| 파일 | 역할 |
|---|---|
| `make_targets.py` | 영양성분 CSV → 대상 품목보고번호 목록(targets.txt) |
| `fetch_ingredients.py` | 식품안전나라 C002 API → 전성분(ingredients.json) |
| `csv_nutrition.py` | 영양성분 단건 확인용 |
| `build_products.py` | 영양성분+전성분 → products.json (알레르기·카테고리 자동) |
| `nukki_batch.py` | 상품 사진 배경제거 → public/products/*.jpg |

## 자동 / 수기
| 항목 | 자동 | 비고 |
|---|---|---|
| 제품명·제조사·분류·영양성분 | ✅ | 공공데이터 |
| 전성분·알레르기(contains) | ✅ | C002 API + 키워드 |
| 상품 이미지 | ✅ 누끼 | 원본 사진은 자체몰 등에서 수집 |
| 원산지 세부 / 교차오염(같은 시설) | ✋ | 공공데이터에 없음 → 필요시 라벨 참고 수기 |
