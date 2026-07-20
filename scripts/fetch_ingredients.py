#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
전성분(원재료) 수집 스크립트 — 식품안전나라 OpenAPI
------------------------------------------------------------------
'식품(첨가물)품목제조보고(원재료)' API 를 호출해서
{ 품목보고번호: 전성분문자열 } 형태의 ingredients.json 을 만듭니다.
그 파일을 build_products.py 의 --ingredients 로 넣으면 됩니다.

■ 준비
    pip install requests

■ 인증키 (비밀번호처럼 관리 — 코드에 하드코딩 금지)
    윈도우 cmd:   set FOOD_API_KEY=발급받은_인증키
    맥/리눅스:    export FOOD_API_KEY=발급받은_인증키

■ 사용법
    # 1) 먼저 구조 확인 (첫 페이지만 받아 필드 이름 출력)
    python scripts/fetch_ingredients.py --service 서비스ID --probe

    # 2) 전체 수집
    python scripts/fetch_ingredients.py --service 서비스ID --out ingredients.json

  · 서비스ID: 미리보기/명세에 나오는 서비스명 (예: I2790 같은 코드)
  · 식품안전나라 URL 규격:
      http://openapi.foodsafetykorea.go.kr/api/{KEY}/{서비스ID}/json/{시작}/{끝}
------------------------------------------------------------------
"""
import argparse, json, os, sys, time
try:
    import requests
except ImportError:
    sys.exit("requests 가 필요해요:  pip install requests")

BASE = "http://openapi.foodsafetykorea.go.kr/api"

# 응답에서 '품목보고번호'/'원재료' 필드를 자동 탐지하기 위한 후보
BOGO_HINTS = ["PRDLST_REPORT_NO", "REPORT_NO", "품목보고", "품목제조보고"]
ING_HINTS  = ["RAWMTRL_NM", "RAWMTRL_NAME", "RAWMTRL", "원재료", "MTRL"]

def pick_field(keys, hints):
    for h in hints:
        for k in keys:
            if h.upper() in k.upper():
                return k
    return None

def fetch_page(key, service, start, end):
    url = f"{BASE}/{key}/{service}/json/{start}/{end}"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    data = r.json()
    # 식품안전나라 응답: { "<service>": { "total_count": "...", "row":[...], "RESULT":{...} } }
    body = data.get(service) or next((v for v in data.values() if isinstance(v, dict)), {})
    rows = body.get("row", []) if isinstance(body, dict) else []
    total = int(body.get("total_count", 0)) if isinstance(body, dict) else 0
    result = body.get("RESULT", {}) if isinstance(body, dict) else {}
    return rows, total, result

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--service", required=True, help="식품안전나라 서비스ID")
    ap.add_argument("--key", default=os.environ.get("FOOD_API_KEY"), help="인증키(기본: 환경변수 FOOD_API_KEY)")
    ap.add_argument("--out", default="ingredients.json")
    ap.add_argument("--page-size", type=int, default=1000)
    ap.add_argument("--max", type=int, default=0, help="최대 수집 건수(0=전체)")
    ap.add_argument("--bogo-field", help="품목보고번호 필드명(자동탐지 실패 시 지정)")
    ap.add_argument("--ing-field", help="원재료명 필드명(자동탐지 실패 시 지정)")
    ap.add_argument("--probe", action="store_true", help="첫 페이지만 받아 필드 구조 출력")
    args = ap.parse_args()
    if not args.key:
        sys.exit("인증키가 없어요. --key 를 주거나 환경변수 FOOD_API_KEY 를 설정하세요.")

    rows, total, result = fetch_page(args.key, args.service, 1, 5 if args.probe else args.page_size)
    if not rows:
        print("응답에 row 가 없어요. RESULT:", result)
        print("→ 서비스ID/인증키/일일 호출한도를 확인하세요.")
        return
    keys = list(rows[0].keys())
    bogo_f = args.bogo_field or pick_field(keys, BOGO_HINTS)
    ing_f  = args.ing_field  or pick_field(keys, ING_HINTS)

    if args.probe:
        print("총 건수:", total)
        print("필드 목록:", keys)
        print("탐지된 품목보고번호 필드:", bogo_f)
        print("탐지된 원재료명 필드:", ing_f)
        print("\n첫 행 예시:")
        print(json.dumps(rows[0], ensure_ascii=False, indent=1))
        print("\n※ 필드가 잘못 탐지됐으면 --bogo-field / --ing-field 로 지정하세요.")
        return

    if not bogo_f or not ing_f:
        sys.exit(f"필드 자동탐지 실패. --probe 로 필드명 확인 후 --bogo-field/--ing-field 지정.\n필드들: {keys}")

    out, start = {}, 1
    while True:
        end = start + args.page_size - 1
        rows, total, result = fetch_page(args.key, args.service, start, end)
        if not rows:
            break
        for r in rows:
            bogo = str(r.get(bogo_f, "")).strip()
            ing = str(r.get(ing_f, "")).strip()
            if bogo and ing:
                out[bogo] = ing
        print(f"  {min(end, total)}/{total} 수집... (누적 {len(out)})")
        if args.max and len(out) >= args.max:
            break
        if end >= total:
            break
        start = end + 1
        time.sleep(0.3)

    json.dump(out, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n완료: {len(out)}개 품목의 전성분 → {args.out}")

if __name__ == "__main__":
    main()
