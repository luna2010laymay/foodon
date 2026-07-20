#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
targets.txt 만들기 — 영양성분 CSV 에서 원하는 상품의 '품목보고번호' 목록을 뽑아요.
------------------------------------------------------------------
사용법:
  # 제조사에 '풀무원' 들어간 상품 전부
  python scripts/make_targets.py --csv 영양성분.csv --brand 풀무원 --out targets.txt

  # 제품명에 '두유' 들어간 상품
  python scripts/make_targets.py --csv 영양성분.csv --name 두유 --out targets.txt

  # 여러 조건(하나라도 맞으면 포함) + 최대 개수 제한
  python scripts/make_targets.py --csv 영양성분.csv --brand 풀무원 --brand 올가 --limit 200 --out targets.txt
------------------------------------------------------------------
"""
import argparse, csv, sys

def load(path):
    for enc in ("cp949", "utf-8-sig", "utf-8"):
        try:
            return list(csv.DictReader(open(path, encoding=enc, newline="")))
        except UnicodeDecodeError:
            continue
    sys.exit("CSV 인코딩을 읽지 못했어요.")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--brand", action="append", default=[], help="제조사명 부분일치(여러 번 가능)")
    ap.add_argument("--name", action="append", default=[], help="제품명 부분일치(여러 번 가능)")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", default="targets.txt")
    args = ap.parse_args()
    if not args.brand and not args.name:
        sys.exit("--brand 또는 --name 중 하나는 필요해요.")

    rows = load(args.csv)
    seen, picked = set(), []
    for r in rows:
        brand = r.get("제조사명", ""); name = r.get("식품명", "")
        ok = any(b in brand for b in args.brand) or any(n in name for n in args.name)
        if not ok:
            continue
        bogo = r.get("품목제조보고번호", "").strip()
        if bogo and bogo not in seen:
            seen.add(bogo); picked.append((bogo, name, brand))
        if args.limit and len(picked) >= args.limit:
            break

    with open(args.out, "w", encoding="utf-8") as f:
        for bogo, _, _ in picked:
            f.write(bogo + "\n")
    print(f"{len(picked)}개 품목보고번호 → {args.out}")
    for bogo, name, brand in picked[:10]:
        print(f"  {bogo}  {name} · {brand}")
    if len(picked) > 10:
        print(f"  ... 외 {len(picked)-10}개")

if __name__ == "__main__":
    main()
