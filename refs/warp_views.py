# 참고 그림을 모델 실루엣에 맞춰 변형: 세로는 폭 프로필을 DTW로 정렬, 가로는 행마다 실루엣 폭에 맞춰 늘린다
import sys, json
import numpy as np
from PIL import Image
n, sildir = sys.argv[1], sys.argv[2]
S = 512
def fg_mask(a):
    bg = a[2, 2].astype(np.float32); a = a.astype(np.float32)
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    grey = (np.abs(r - g) < 14) & (np.abs(g - b) < 14) & (r > 100)  # 발밑 회색 그림자
    return (np.abs(a - bg).sum(2) > 60) & ~((b > r + 12) & (b >= g)) & ~grey
def profile(mask):
    rows = np.where(mask.any(1))[0]; r0, r1 = rows[0], rows[-1] + 1
    ext = []
    for r in range(r0, r1):
        cols = np.where(mask[r])[0]; ext.append((cols[0], cols[-1] + 1) if len(cols) else (np.nan, np.nan))
    ext = np.array(ext, dtype=np.float32)
    # 빈 행은 이웃으로 보간
    for k in range(2):
        v = ext[:, k]; idx = np.arange(len(v)); good = ~np.isnan(v); v[~good] = np.interp(idx[~good], idx[good], v[good])
    return r0, r1, ext
def dtw(a, b):
    # a: 모델 프로필(폭), b: 그림 프로필(폭). 길이가 다르니 리샘플 없이 DTW로 행 대응을 구한다
    na, nb = len(a), len(b); D = np.full((na + 1, nb + 1), np.inf); D[0, 0] = 0
    cost = (a[:, None] - b[None, :]) ** 2
    for i in range(1, na + 1):
        for j in range(max(1, i * nb // na - 40), min(nb + 1, i * nb // na + 41)):
            D[i, j] = cost[i - 1, j - 1] + min(D[i - 1, j], D[i, j - 1], D[i - 1, j - 1])
    i, j = na, nb; m = np.zeros(na)
    acc = [[] for _ in range(na)]
    while i > 0 and j > 0:
        acc[i - 1].append(j - 1)
        k = np.argmin([D[i - 1, j - 1], D[i - 1, j], D[i, j - 1]])
        if k == 0: i -= 1; j -= 1
        elif k == 1: i -= 1
        else: j -= 1
    for r in range(na): m[r] = np.mean(acc[r]) if acc[r] else (m[r - 1] if r else 0)
    # 단조 증가·부드럽게
    m = np.maximum.accumulate(m); k = 9; m = np.convolve(np.pad(m, (k // 2, k // 2), 'edge'), np.ones(k) / k, 'valid')
    return m
def fill_outside(col, known, iters=120):
    col = col.copy(); known = known.copy()
    for _ in range(iters):
        if known.all(): break
        acc = np.zeros_like(col); cnt = np.zeros(known.shape, np.float32)
        for dy, dx in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
            k = np.roll(known, (dy, dx), (0, 1)); c = np.roll(col, (dy, dx), (0, 1)); acc += c * k[..., None]; cnt += k
        new = (~known) & (cnt > 0); col[new] = acc[new] / cnt[new][:, None]; known |= new
    return col
for view, imgname, mirror in (('front', 'front', False), ('back', 'back', False), ('side', 'side', False), ('side_r', 'side', True)):
    sil = np.asarray(Image.open(f'{sildir}/sil_{"side" if view == "side_r" else view}.png').convert('RGBA'))[:, :, 3] > 128
    if mirror: sil = sil[:, ::-1]
    img = np.asarray(Image.open(f'views/{n}_{imgname}.png').convert('RGB'))
    if mirror: img = img[:, ::-1]
    im_mask = fg_mask(img)
    mr0, mr1, mext = profile(sil); ir0, ir1, iext = profile(im_mask)
    mw = mext[:, 1] - mext[:, 0]; iw = iext[:, 1] - iext[:, 0]
    rowmap = dtw(mw / mw.max(), iw / iw.max())  # 모델 행 r → 그림 행(상대)
    linear = np.arange(mr1 - mr0) * (ir1 - ir0) / (mr1 - mr0)
    dev = np.abs(rowmap - linear).max() / (ir1 - ir0)
    if dev > 0.15: rowmap = linear; print('  dtw deviates', round(float(dev), 2), '-> linear')
    else: print('  dtw ok', round(float(dev), 2))
    out = np.zeros((S, S, 3), np.float32); known = np.zeros((S, S), bool)
    H, W = img.shape[:2]
    for r in range(mr0, mr1):
        ir = int(round(ir0 + rowmap[r - mr0])); ir = min(max(ir, ir0), ir1 - 1)
        mx0, mx1 = mext[r - mr0]; ix0, ix1 = iext[ir - ir0]
        cols = np.arange(int(mx0), int(mx1))
        if len(cols) == 0 or ix1 - ix0 < 1: continue
        t = (cols - mx0) / max(mx1 - mx0, 1); src = np.clip((ix0 + t * (ix1 - ix0)).astype(int), 0, W - 1)
        out[r, cols] = img[ir, src]; known[r, cols] = True
    out = fill_outside(out, known)
    Image.fromarray(out.clip(0, 255).astype(np.uint8)).save(f'views/{n}_{view}_warp.png')
    print(view, 'rows model', mr1 - mr0, 'img', ir1 - ir0)
