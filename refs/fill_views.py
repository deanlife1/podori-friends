# 투영용 그림: 배경을 가장 가까운 캐릭터 색으로 채워 가장자리에 흰/파란색이 번지지 않게 하고, 캐릭터의 화소 범위를 기록한다
import sys, json
from PIL import Image
import numpy as np
out = {}
for n in ('bear', 'tiger'):
    for v in ('front', 'back', 'side', 'side_r'):
        try: im = Image.open(f'views/{n}_{v}.png').convert('RGB')
        except FileNotFoundError: continue
        a = np.asarray(im).astype(np.float32); bg = a[2, 2]
        fg = (np.abs(a - bg).sum(2) > 60) & ~((a[:, :, 2] > a[:, :, 0] + 12) & (a[:, :, 2] >= a[:, :, 1]))
        ys, xs = np.where(fg); H, W = fg.shape
        out[f'{n}_{v}'] = [float(xs.min() / W), float(ys.min() / H), float((xs.max() + 1) / W), float((ys.max() + 1) / H)]
        col = a.copy(); known = fg.copy()
        for _ in range(90):
            if known.all(): break
            acc = np.zeros_like(col); cnt = np.zeros(known.shape, np.float32)
            for dy, dx in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
                k = np.roll(known, (dy, dx), (0, 1)); c = np.roll(col, (dy, dx), (0, 1))
                acc += c * k[..., None]; cnt += k
            new = (~known) & (cnt > 0)
            col[new] = acc[new] / cnt[new][:, None]; known |= new
        Image.fromarray(col.clip(0, 255).astype(np.uint8)).save(f'views/{n}_{v}_fill.png')
json.dump(out, open('views/bounds.json', 'w'), indent=1); print(json.dumps(out))
