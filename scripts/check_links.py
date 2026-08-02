#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
쿠팡(및 기타 shopUrl) 상품 링크 생존확인기.
- src/products.json 의 모든 shopUrl 을 접속 테스트해서
  살아있음 / 품절 / 삭제 / 차단 / 오류 로 분류하고 link_check_report.md 를 생성한다.
- GitHub Actions(외부 네트워크 자유) 또는 개인 PC에서 실행 가능.
  (foodon 작업 샌드박스는 외부접속이 막혀 있어 여기선 대부분 '차단/오류'로 나온다.)
"""
import json, sys, time, re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

try:
    import requests
except ImportError:
    sys.exit("requests 필요:  pip install requests")

ROOT = __file__.rsplit("/scripts/", 1)[0]
PRODUCTS = ROOT + "/src/products.json"
REPORT = ROOT + "/link_check_report.md"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
HEADERS = {"User-Agent": UA, "Accept-Language": "ko-KR,ko;q=0.9",
           "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}

# 페이지 본문에서 품절/삭제를 시사하는 문구 (soft-404 대응)
SOLDOUT_KW = ["일시품절", "일시 품절", "품절되었", "재입고", "판매가 종료", "판매 종료",
              "판매중지", "판매가 중지", "현재 판매하지"]
DEAD_KW = ["상품을 찾을 수 없", "존재하지 않는", "삭제된 상품", "페이지를 찾을 수 없",
           "잘못된 접근", "상품이 존재하지"]

STATUS = {  # 코드: (이모지, 라벨)
    "ALIVE": ("✅", "살아있음"),
    "SOLD_OUT": ("⚠️", "품절"),
    "DEAD": ("❌", "삭제/없음"),
    "BLOCKED": ("🚫", "접속차단(봇탐지)"),
    "ERROR": ("⁉️", "확인불가(오류)"),
}
ORDER = ["DEAD", "SOLD_OUT", "BLOCKED", "ERROR", "ALIVE"]  # 문제 먼저


def classify(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
    except requests.exceptions.RequestException as e:
        return "ERROR", "-", str(e)[:60]
    code = r.status_code
    body = (r.text or "")[:200000]
    if code in (403, 429):
        return "BLOCKED", code, "봇 차단 추정"
    if code in (404, 410):
        return "DEAD", code, "페이지 없음"
    if code >= 500:
        return "ERROR", code, "서버 오류"
    if code == 200:
        for kw in DEAD_KW:
            if kw in body:
                return "DEAD", code, f"본문: '{kw}'"
        for kw in SOLDOUT_KW:
            if kw in body:
                return "SOLD_OUT", code, f"본문: '{kw}'"
        return "ALIVE", code, "정상"
    return "ERROR", code, "예상외 응답"


def check(item):
    time.sleep(0.15)  # 예의상 소량 지연
    st, code, note = classify(item["shopUrl"])
    return {**item, "status": st, "http": code, "note": note}


def main():
    data = json.load(open(PRODUCTS, encoding="utf-8"))
    targets = [{"id": x["id"], "name": x["name"], "shopUrl": x["shopUrl"]}
               for x in data if x.get("shopUrl")]
    print(f"확인 대상: {len(targets)}개")
    results = []
    if targets:
        with ThreadPoolExecutor(max_workers=8) as ex:
            results = list(ex.map(check, targets))

    counts = {k: 0 for k in STATUS}
    for r in results:
        counts[r["status"]] += 1
    results.sort(key=lambda r: (ORDER.index(r["status"]), r["id"]))

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = []
    lines.append("# 쿠팡 링크 생존확인 리포트")
    lines.append("")
    lines.append(f"_최종 확인: {now} · 대상 {len(targets)}개_")
    lines.append("")
    summary = " · ".join(f"{STATUS[k][0]} {STATUS[k][1]} {counts[k]}" for k in ORDER)
    lines.append(f"**요약:** {summary}")
    lines.append("")
    problems = [r for r in results if r["status"] != "ALIVE"]
    if not problems and targets:
        lines.append("🎉 모든 링크 정상(살아있음).")
        lines.append("")
    lines.append("| id | 상품명 | 상태 | HTTP | 비고 | 링크 |")
    lines.append("|---|---|---|---|---|---|")
    for r in results:
        emo, lab = STATUS[r["status"]]
        nm = r["name"].replace("|", "/")
        lines.append(f"| {r['id']} | {nm} | {emo} {lab} | {r['http']} | {r['note']} | "
                     f"[열기]({r['shopUrl']}) |")
    if not targets:
        lines.append("")
        lines.append("_등록된 shopUrl이 없습니다._")

    open(REPORT, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(f"리포트 작성: {REPORT}")
    print("요약:", {k: counts[k] for k in ORDER})


if __name__ == "__main__":
    main()
