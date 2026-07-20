#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
전성분(원재료) 수집 스크립트 — 식품안전나라 OpenAPI (서비스 C002)
------------------------------------------------------------------
'식품(첨가물)품목제조보고(원재료)' API 를 호출해서
{ 품목보고번호: 전성분문자열 } 형태의 ingredients.json 을 만듭니다.

API 규격 (식품안전나라):
  http://openapi.foodsafetykorea.go.kr/api/{인증키}/C002/json/{시작}/{끝}/PRDLST_REPORT_NO={품목보고번호}
  · 품목보고번호 필드 : PRDLST_REPORT_NO
  · 원재료명(전성분) 필드 : RAWMTRL_NM
  · 하루 1000회 호출 제한

■ 준비 :  pip install requests
■ 인증키 등록 :
    윈도우 cmd :  set FOOD_API_KEY=발급받은키
    맥/리눅스   :  export FOOD_API_KEY=발급받은키

■ 사용법
    # (1) 키 없이 구조/연결 확인 (샘플 데이터)
    python scripts/fetch_ingredients.py --probe

    # (2) 품목보고번호 목록으로 전성분 수집 (targets.txt: 한 줄에 하나)
    python scripts/fetch_ingredients.py --targets targets.txt --out ingredients.json
------------------------------------------------------------------
"""
import argparse, json, os, sys, time
try:
    import requests
except ImportError:
    sys.exit("requests 가 필요해요:  pip install requests")

BASE = "http://openapi.foodsafetykorea.go.kr/api"
SERVICE = "C002"
BOGO_FIELD = "PRDLST_REPORT_NO"
ING_FIELD = "RAWMTRL_NM"
ORD_HINTS = ["DISPOS_ORD", "표시순서", "SORT", "ORD"]

def pick(keys, hints):
    for h in hints:
        for k in keys:
            if h.upper() in str(k).upper():
                return k
    return None

def get_rows(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    data = r.json()
    body = data.get(SERVICE) or next((v for v in data.values() if isinstance(v, dict)), {})
    rows = body.get("row", []) if isinstance(body, dict) else []
    result = body.get("RESULT", {}) if isinstance(body, dict) else {}
    return rows, result

def join_ingredients(rows):
    """여러 행(성분별 1행)일 수 있으니 표시순서로 합침. 한 행에 전체가 있으면 그대로."""
    if not rows:
        return ""
    ing_f = ING_FIELD if ING_FIELD in rows[0] else pick(rows[0].keys(), ["RAWMTRL", "원재료"])
    ord_f = pick(rows[0].keys(), ORD_HINTS)
    if len(rows) > 1 and ord_f:
        try:
            rows = sorted(rows, key=lambda r: int(str(r.get(ord_f) or 0)))
        except ValueError:
            pass
    vals = [str(r.get(ing_f, "")).strip() for r in rows]
    vals = [v for v in vals if v]
    if len(vals) == 1:
        return vals[0]
    return ",".join(vals)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", default=os.environ.get("FOOD_API_KEY"))
    ap.add_argument("--targets", help="품목보고번호 목록 파일(한 줄에 하나)")
    ap.add_argument("--out", default="ingredients.json")
    ap.add_argument("--probe", action="store_true", help="키 없이 샘플로 구조 확인")
    ap.add_argument("--sleep", type=float, default=0.25, help="호출 간 대기(초)")
    args = ap.parse_args()

    # (1) 구조 확인 — 'sample' 키는 인증키 없이 예시 데이터를 줘요
    if args.probe:
        rows, result = get_rows(f"{BASE}/sample/{SERVICE}/json/1/5")
        if not rows:
            print("샘플 응답이 비었어요. RESULT:", result); return
        print("연결 OK! 필드 목록:", list(rows[0].keys()))
        print(f"품목보고번호 필드: {BOGO_FIELD} / 원재료명 필드: {ING_FIELD}")
        print("\n첫 행 예시:")
        print(json.dumps(rows[0], ensure_ascii=False, indent=1))
        return

    if not args.key:
        sys.exit("인증키가 없어요. 환경변수 FOOD_API_KEY 설정 또는 --key 사용.")
    if not args.targets or not os.path.exists(args.targets):
        sys.exit("--targets 파일이 필요해요 (품목보고번호 목록).")

    targets = [l.strip() for l in open(args.targets, encoding="utf-8") if l.strip()]
    # 이어받기: 이미 있는 결과는 건너뜀
    out = {}
    if os.path.exists(args.out):
        try: out = json.load(open(args.out, encoding="utf-8"))
        except Exception: out = {}

    done, fail = 0, []
    for i, bogo in enumerate(targets, 1):
        if bogo in out:
            continue
        url = f"{BASE}/{args.key}/{SERVICE}/json/1/50/{BOGO_FIELD}={bogo}"
        try:
            rows, result = get_rows(url)
            ing = join_ingredients(rows)
            if ing:
                out[bogo] = ing; done += 1
            else:
                fail.append(bogo)
        except Exception as e:
            fail.append(bogo)
            print(f"  [{i}/{len(targets)}] {bogo} 오류: {e}", file=sys.stderr)
        if i % 20 == 0 or i == len(targets):
            print(f"  {i}/{len(targets)} 진행... (수집 {len(out)})")
            json.dump(out, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        time.sleep(args.sleep)

    json.dump(out, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n완료: {len(out)}개 전성분 → {args.out}")
    if fail:
        print(f"전성분 못 찾음 {len(fail)}개(품목보고번호 불일치 가능): {fail[:5]}")

if __name__ == "__main__":
    main()
