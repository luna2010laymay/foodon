# 실행 런북 — 풀무원 전성분 → products.json (id 31~)

이 문서는 "풀무원 상품 전성분 수집 → products.json 생성" 1회 실행 절차입니다.
대상 품목보고번호 56개는 `data/targets_pulmuone.txt` 에 이미 뽑아 두었습니다.

## 왜 전성분 수집만 로컬(또는 HTTP 되는 곳)에서?

전성분 API(식품안전나라 C002)는 **HTTP 전용**입니다.
`http://openapi.foodsafetykorea.go.kr/api/{키}/C002/json/...`

클라우드 세션 등 **HTTPS만 허용하는 egress 프록시** 환경에서는 이 평문 HTTP 호출이
차단됩니다. (data.go.kr 의 "식품(첨가물)품목제조보고(원재료)" 15062098 은 자체 REST 가
아니라 같은 C002 로 연결되는 **LINK 타입**이라 우회가 되지 않습니다.)

→ 그래서 **전성분 수집(2단계)만** 인터넷(HTTP)이 열린 곳에서 실행하고,
   나머지는 어디서든 됩니다.

## 1회 실행 (인터넷 되는 PC)

```bash
# 준비
pip install requests
cd foodon
git pull

# 인증키 등록 (식품안전나라 C002 키)
#   윈도우 cmd:  set FOOD_API_KEY=발급받은키
#   맥/리눅스 :  export FOOD_API_KEY=발급받은키

# ── 전성분 수집 (이 한 줄만 HTTP 필요) ──
python scripts/fetch_ingredients.py --targets data/targets_pulmuone.txt --out ingredients.json
```

`ingredients.json` 은 `{ "품목보고번호": "정제수,토마토페이스트,...", ... }` 형태입니다.
이 파일 내용을 **채팅에 붙여넣어** 주시면 이후(빌드·병합·커밋)는 제가 마무리합니다.

또는 직접 끝까지 실행하려면:

```bash
python scripts/build_products.py \
    --nutri-csv 영양성분.csv \
    --ingredients ingredients.json \
    --targets data/targets_pulmuone.txt \
    --start-id 31 --out products_new.json
```

→ `products_new.json` 항목을 `src/products.json` 배열 뒤에 붙여넣으면 앱에 반영됩니다.
   (전성분·알레르기 contains·성분 라벨 allergy/additive 자동 태깅)

## 참고 — 지금(전성분 없이) 미리 만든 것

CSV(영양성분) 만으로도 아래는 **네트워크 없이** 생성됩니다.
`python scripts/build_products.py --nutri-csv 영양성분.csv --targets data/targets_pulmuone.txt --start-id 31 --out products_new.json`
→ 56개 상품의 영양성분·분류(cat)·브랜드·이미지 경로가 채워지고, `ing` 만 빈 배열([])로
   남습니다. 이후 전성분을 얻으면 `--ingredients` 를 붙여 다시 돌리면 전부 채워집니다.
