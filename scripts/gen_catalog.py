#!/usr/bin/env python3
# 전체 상품 카탈로그(원재료+사진) HTML 생성 → public/catalog.html
# 라이브: https://foodon-nine.vercel.app/catalog.html
import json, html, os

d = json.load(open('src/products.json'))
d.sort(key=lambda x: (x.get('cat', ''), x['id']))

def ing_names(p):
    """전성분 이름 목록과 알레르기 여부 반환: [(name, is_allergy), ...] (그룹은 [그룹명] 접두)"""
    out = []
    if 'ingGroups' in p:
        for g in p['ingGroups']:
            out.append(('【' + g.get('name', '') + '】', False))
            for it in g.get('ing', []):
                nm = it[0] if isinstance(it, list) else str(it)
                lb = it[1] if isinstance(it, list) and len(it) > 1 else []
                out.append((nm, 'allergy' in lb))
    else:
        for it in p.get('ing', []):
            nm = it[0] if isinstance(it, list) else str(it)
            lb = it[1] if isinstance(it, list) and len(it) > 1 else []
            out.append((nm, 'allergy' in lb))
    return out

cards = []
cur_cat = None
cats_order = []
for p in d:
    cat = p.get('cat', '기타')
    if cat != cur_cat:
        cur_cat = cat
        cats_order.append(cat)
        cards.append(f'<h2 class="cat" id="cat-{html.escape(cat)}">{html.escape(cat)}</h2>')
    name = html.escape(p.get('name', ''))
    brand = html.escape(p.get('brand', ''))
    img = html.escape(p.get('img', ''))
    ings = ing_names(p)
    ing_html = ' · '.join(
        (f'<b class="al">{html.escape(n)}</b>' if a else html.escape(n)) for n, a in ings
    ) or '<span class="muted">전성분 정보 없음</span>'
    contains = p.get('contains', [])
    facility = p.get('facility', [])
    badges = ''
    if contains:
        badges += ''.join(f'<span class="b b-c">{html.escape(c)}</span>' for c in contains)
    if facility:
        badges += ''.join(f'<span class="b b-f">{html.escape(fx)}</span>' for fx in facility)
    kcal = ''
    n = p.get('nutrition')
    if n and n.get('kcal'):
        kcal = f'<span class="kcal">{n.get("serving","")} · {n["kcal"]}kcal</span>'
    cards.append(f'''<div class="card">
  <img loading="lazy" src="{img}" alt="{name}">
  <div class="info">
    <div class="nm">{name}</div>
    <div class="meta"><span class="brand">{brand}</span> {kcal}</div>
    <div class="ing">{ing_html}</div>
    <div class="badges">{badges}</div>
  </div>
</div>''')

nav = ' '.join(
    f'<a href="#cat-{html.escape(c)}">{html.escape(c)}</a>' for c in cats_order
)

page = f'''<!doctype html>
<html lang="ko"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>푸드온 전체 상품 카탈로그 ({len(d)}개)</title>
<style>
 :root{{--bg:#fafaf7;--card:#fff;--line:#eceae4;--muted:#9a968c;--al:#d33;--c:#c2410c;--f:#6b7280;}}
 *{{box-sizing:border-box}}
 body{{margin:0;background:var(--bg);color:#2a2a28;font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Malgun Gothic",sans-serif;line-height:1.5}}
 header{{position:sticky;top:0;background:rgba(250,250,247,.96);backdrop-filter:blur(6px);border-bottom:1px solid var(--line);padding:12px 16px;z-index:10}}
 header h1{{margin:0 0 6px;font-size:18px}}
 .nav{{font-size:12px;line-height:1.9}}
 .nav a{{color:#555;text-decoration:none;background:#fff;border:1px solid var(--line);border-radius:20px;padding:2px 9px;margin-right:3px;white-space:nowrap;display:inline-block}}
 main{{max-width:1100px;margin:0 auto;padding:8px 12px 60px}}
 h2.cat{{font-size:16px;margin:26px 4px 10px;padding-bottom:6px;border-bottom:2px solid #e0ddd4;scroll-margin-top:120px}}
 .card{{display:flex;gap:12px;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:10px;margin-bottom:8px}}
 .card img{{width:88px;height:88px;object-fit:contain;border-radius:8px;background:#fff;flex:0 0 auto}}
 .info{{min-width:0;flex:1}}
 .nm{{font-weight:700;font-size:14.5px}}
 .meta{{font-size:12px;color:var(--muted);margin:1px 0 5px}}
 .brand{{color:#7a756a;font-weight:600}}
 .kcal{{margin-left:6px}}
 .ing{{font-size:12.5px;color:#444;word-break:keep-all}}
 .ing b.al{{color:var(--al);font-weight:700}}
 .muted{{color:var(--muted)}}
 .badges{{margin-top:6px;display:flex;flex-wrap:wrap;gap:4px}}
 .b{{font-size:11px;padding:1px 7px;border-radius:20px;border:1px solid}}
 .b-c{{color:var(--c);border-color:#f4c9a8;background:#fff5ee}}
 .b-f{{color:var(--f);border-color:#e2e5ea;background:#f6f7f9}}
 .legend{{font-size:12px;color:#666;margin:4px 0 0}}
 .legend b.al{{color:var(--al)}}
 @media(max-width:480px){{.card img{{width:70px;height:70px}}}}
</style></head>
<body>
<header>
 <h1>푸드온 전체 상품 카탈로그 · {len(d)}개</h1>
 <div class="legend"><b class="al">빨강</b>=알레르기 유발성분 · <span style="color:#c2410c">주황뱃지</span>=함유 · <span style="color:#6b7280">회색뱃지</span>=같은시설 혼입가능</div>
 <div class="nav">{nav}</div>
</header>
<main>
{''.join(cards)}
</main>
</body></html>'''

os.makedirs('public', exist_ok=True)
open('public/catalog.html', 'w').write(page)
print('생성:', 'public/catalog.html', f'({len(d)}개, {len(page)//1024}KB)')
