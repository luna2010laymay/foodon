#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
누끼 배치 스크립트 (푸드온)
------------------------------------------------------------------
상품 원본 사진 폴더를 통째로 넣으면, 각 사진의 배경을 제거하고
'흰 배경 + 중앙 정렬 + 정사각형' JPEG 로 만들어 줍니다.
그대로 public/products/ 에 넣어 앱에서 바로 쓸 수 있어요.

■ 준비 (한 번만)
    pip install pillow numpy scipy
    # (선택) AI 배경제거를 쓰려면:  pip install rembg onnxruntime
    #   → 처음 실행 시 모델(u2net)을 자동 다운로드하므로 인터넷 필요.

■ 사용법
    python scripts/nukki_batch.py --indir raw --outdir public/products

    raw/ 폴더에 원본 사진(jpg/png/webp)을 넣어두면,
    outdir 에 같은 파일명(확장자만 .jpg)으로 저장됩니다.

■ 배경제거 방식 (--method)
    auto  (기본) : rembg 가 설치돼 있으면 rembg, 없으면 flood 사용
    rembg        : AI 배경제거(어떤 배경이든 깔끔) — 인터넷/모델 필요
    flood        : 테두리 색 기준 채우기(밝은/단색 배경에 적합, 오프라인)

■ 자주 쓰는 옵션
    --size 340         출력 정사각 크기(px)              (기본 340)
    --pad 0.10         상품 주변 여백 비율               (기본 0.10)
    --flood-thr 32     flood 배경색 허용 오차(클수록 많이 지움)
    --keep-largest     flood 후 가장 큰 덩어리만 남김(주변 잡티 제거)
                       * 흰 상품이 흰 배경일 땐 끄는 게 안전(기본 꺼짐)
    --quality 82       JPEG 품질                         (기본 82)
    --ext jpg|png      출력 포맷                          (기본 jpg)
    --overwrite        이미 있는 결과도 덮어쓰기

■ 입력 사진 팁 (중요)
    · 가장 좋은 입력은 "상품 하나만" 찍힌 대표 이미지(자체몰 대표컷 등)예요.
      → 이런 사진은 배경만 깔끔히 지워 흰 배경 중앙정렬로 완성됩니다.
    · 배지·비교 그림·여러 상품이 섞인 '홍보용 합성 이미지'는
      배경제거로 지워지지 않아요(실제 사물로 인식). 필요한 부분만
      잘라서 넣어 주세요. (rembg 도 여러 피사체는 다 남깁니다.)
------------------------------------------------------------------
"""
import argparse, os, sys, traceback
import numpy as np
from PIL import Image, ImageOps

IN_EXT = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif")

# ---------------------------------------------------------------- rembg (선택)
_REMBG = {"tried": False, "session": None, "ok": False}
def get_rembg_session():
    if not _REMBG["tried"]:
        _REMBG["tried"] = True
        try:
            from rembg import new_session
            _REMBG["session"] = new_session()   # 첫 호출 시 모델 다운로드(인터넷)
            _REMBG["ok"] = True
        except Exception as e:
            print(f"  [rembg 사용 불가 → flood 로 대체] {e}", file=sys.stderr)
            _REMBG["ok"] = False
    return _REMBG["session"] if _REMBG["ok"] else None

# ---------------------------------------------------------------- 유틸
def load_rgb(path):
    """EXIF 회전 보정 + 투명 PNG는 흰 배경 합성 → RGB 반환."""
    im = Image.open(path)
    im = ImageOps.exif_transpose(im)
    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
        im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        im = Image.alpha_composite(bg, im).convert("RGB")
    else:
        im = im.convert("RGB")
    return im

def remove_bg_rembg(im, session):
    """rembg 로 배경 제거 → 흰 배경 RGB + content mask(bool)."""
    from rembg import remove
    out = remove(im, session=session)          # RGBA (배경 투명)
    if out.mode != "RGBA":
        out = out.convert("RGBA")
    a = np.asarray(out)
    alpha = a[:, :, 3]
    rgb = a[:, :, :3].astype(np.int32)
    mask = alpha > 12
    white = np.where(mask[:, :, None], rgb, 255).astype(np.uint8)
    return Image.fromarray(white), mask

def remove_bg_flood(im, thr, keep_largest):
    """테두리 색 기준 flood-fill 로 배경을 흰색으로 → 흰 배경 RGB + content mask."""
    a = np.asarray(im).astype(np.int32)
    h, w, _ = a.shape
    ring = np.concatenate([a[0:3].reshape(-1, 3), a[-3:].reshape(-1, 3),
                           a[:, 0:3].reshape(-1, 3), a[:, -3:].reshape(-1, 3)])
    bg = np.median(ring, axis=0)
    dist = np.abs(a - bg).sum(axis=2)
    cand = dist <= thr                          # 배경 후보(색이 테두리와 비슷)
    try:
        from scipy import ndimage
        lbl, _ = ndimage.label(cand)
        seed = np.zeros((h, w), bool)
        seed[0, :] = seed[-1, :] = seed[:, 0] = seed[:, -1] = True
        border_labels = set(lbl[seed & cand].tolist()) - {0}
        flood = np.isin(lbl, list(border_labels))
    except Exception:
        flood = _flood_bfs(cand)                # scipy 없을 때 폴백
    fg = ~flood
    if keep_largest:
        try:
            from scipy import ndimage
            lf, nf = ndimage.label(fg)
            if nf > 0:
                sizes = ndimage.sum(np.ones_like(lf), lf, range(1, nf + 1))
                fg = lf == (int(np.argmax(sizes)) + 1)
        except Exception:
            pass
    out = a.copy()
    out[~fg] = [255, 255, 255]
    return Image.fromarray(out.astype(np.uint8)), fg

def _flood_bfs(cand):
    from collections import deque
    h, w = cand.shape
    vis = np.zeros((h, w), bool)
    dq = deque()
    for x in range(w): dq.append((0, x)); dq.append((h - 1, x))
    for y in range(h): dq.append((y, 0)); dq.append((y, w - 1))
    while dq:
        y, x = dq.popleft()
        if y < 0 or y >= h or x < 0 or x >= w or vis[y, x] or not cand[y, x]:
            continue
        vis[y, x] = True
        dq.extend([(y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)])
    return vis

def square_center(rgb_im, mask, size, pad, bg_color):
    """content(mask) 영역만 잘라 흰 정사각 캔버스 가운데 배치 후 리사이즈."""
    a = np.asarray(rgb_im)
    if mask is None or mask.sum() == 0:
        nonwhite = a.sum(axis=2) < 745
        ys, xs = np.where(nonwhite)
    else:
        ys, xs = np.where(mask)
    if len(xs) == 0:
        box = (0, 0, rgb_im.width, rgb_im.height)
    else:
        box = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    crop = rgb_im.crop(box)
    w, h = crop.size
    side = int(max(w, h) * (1 + pad * 2))
    canvas = Image.new("RGB", (side, side), bg_color)
    canvas.paste(crop, ((side - w) // 2, (side - h) // 2))
    return canvas.resize((size, size), Image.LANCZOS)

def process_one(path, method, thr, keep_largest, size, pad, bg_color):
    im = load_rgb(path)
    used = method
    if method in ("auto", "rembg"):
        session = get_rembg_session()
        if session is not None:
            rgb, mask = remove_bg_rembg(im, session); used = "rembg"
        elif method == "rembg":
            raise RuntimeError("rembg 를 쓸 수 없습니다 (설치/모델 확인).")
        else:
            rgb, mask = remove_bg_flood(im, thr, keep_largest); used = "flood"
    else:
        rgb, mask = remove_bg_flood(im, thr, keep_largest); used = "flood"
    return square_center(rgb, mask, size, pad, bg_color), used

def main():
    ap = argparse.ArgumentParser(description="푸드온 누끼 배치 스크립트")
    ap.add_argument("--indir", required=True, help="원본 사진 폴더")
    ap.add_argument("--outdir", required=True, help="결과 저장 폴더")
    ap.add_argument("--method", choices=["auto", "rembg", "flood"], default="auto")
    ap.add_argument("--size", type=int, default=340)
    ap.add_argument("--pad", type=float, default=0.10)
    ap.add_argument("--flood-thr", type=int, default=32)
    ap.add_argument("--keep-largest", action="store_true")
    ap.add_argument("--quality", type=int, default=82)
    ap.add_argument("--ext", choices=["jpg", "png"], default="jpg")
    ap.add_argument("--bg", default="255,255,255", help="배경색 R,G,B")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    bg_color = tuple(int(x) for x in args.bg.split(","))
    os.makedirs(args.outdir, exist_ok=True)
    files = sorted(f for f in os.listdir(args.indir) if f.lower().endswith(IN_EXT))
    if not files:
        print(f"[!] {args.indir} 에 이미지가 없어요.", file=sys.stderr); sys.exit(1)

    ok = skip = fail = 0
    for i, fn in enumerate(files, 1):
        stem = os.path.splitext(fn)[0]
        outp = os.path.join(args.outdir, f"{stem}.{args.ext}")
        if os.path.exists(outp) and not args.overwrite:
            print(f"[{i}/{len(files)}] {fn} → (이미 있음, 건너뜀)"); skip += 1; continue
        try:
            res, used = process_one(os.path.join(args.indir, fn), args.method,
                                    args.flood_thr, args.keep_largest,
                                    args.size, args.pad, bg_color)
            if args.ext == "jpg":
                res.save(outp, "JPEG", quality=args.quality)
            else:
                res.save(outp, "PNG")
            print(f"[{i}/{len(files)}] {fn} → {os.path.basename(outp)}  ({used})")
            ok += 1
        except Exception as e:
            print(f"[{i}/{len(files)}] {fn} → 실패: {e}", file=sys.stderr)
            traceback.print_exc()
            fail += 1

    print(f"\n완료: 성공 {ok} · 건너뜀 {skip} · 실패 {fail}  → {args.outdir}")

if __name__ == "__main__":
    main()
