# _src/*.png  ->  ../img/*.webp
#   green key -> alpha, despill, trim, pad (or cover-crop) to the layer's box ratio, save WebP.
#   keys=2 layers also report where their magenta slots landed, in 1280x900 design space,
#   so the child layers (windows, cells, LCD, fan) can be moved onto them instead of guessed at.
#     py cut.py [name ...]
import json, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage

SRC, IMG = '../_src', '../img'
Q, AQ, BGQ = 82, 88, 76

# where the object sits in its box when the render's aspect does not match it
ANCHOR = {'tower_l': 'bottom', 'tower_r': 'bottom', 'meter': 'bottom', 'moteur': 'bottom',
          'candle': 'bottom', 'house': 'bottom', 'skyline': 'bottom', 'bulb': 'top',
          'rack': 'bottom', 'breaker': 'top'}
# cables and wires: keyed without the morphology that eats a 2px strand
THIN = {'wires', 'cable_in', 'cable_out', 'cable_b'}

# the child layers that get dropped into a host's magenta slots, in reading order
SLOTS = {'inv_body': ['inv_screen', 'fan'],
         'rack':     ['bms', 'cell3', 'cell2', 'cell1'],
         'house':    ['win1', 'win2', 'win3', 'win4']}
# the hosts' own top-left corner in the 1280x900 design space (from LAYOUT in index.html)
HOST_XY = {'inv_body': (428, 212), 'rack': (386, 176), 'house': (286, 188)}
# the icons sheet's three cut-outs and the boxes they have to fit
SHEET_BOX = {'ac': (140, 104), 'wifi': (96, 96), 'fridge': (96, 126)}


def save(img, dst, maxw, q):
    if img.width > maxw:
        img = img.resize((maxw, round(img.height * maxw / img.width)), Image.LANCZOS)
    kw = dict(quality=q, method=6)
    if img.mode == 'RGBA':
        kw['alpha_quality'] = AQ
    img.save(dst, 'WEBP', **kw)
    return img


def blobs(mask, frac=4e-4):
    """connected components, kept by ABSOLUTE area, in reading order (rows top-down, then x)"""
    lab, k = ndimage.label(mask)
    if not k:
        return []
    areas = ndimage.sum(mask, lab, range(1, k + 1))
    floor = mask.size * frac
    keep = [i + 1 for i, a in enumerate(areas) if a > floor]
    boxes = []
    for i in keep:
        ys, xs = np.where(lab == i)
        boxes.append([xs.min(), ys.min(), xs.max() + 1, ys.max() + 1])
    if not boxes:
        return []
    hs = [b[3] - b[1] for b in boxes]
    med = float(np.median(hs))
    boxes.sort(key=lambda b: b[1])
    rows, cur = [], [boxes[0]]
    for b in boxes[1:]:
        if abs(b[1] - cur[0][1]) < med * 0.8:
            cur.append(b)
        else:
            rows.append(cur); cur = [b]
    rows.append(cur)
    return [b for row in rows for b in sorted(row, key=lambda b: b[0])]


def key_green(im, thin=False):
    """alpha from the flat green key, plus the despilled rgb.
    thin=True is for cables and wires: a 2px cable does not survive an opening + erosion,
    and an absolute area floor drops every separate strand."""
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    grn = (g - np.maximum(r, b) > 40)
    fg = ~grn if thin else ndimage.binary_opening(~grn, iterations=2)
    lab, k = ndimage.label(fg)
    if k:
        areas = ndimage.sum(fg, lab, range(1, k + 1))
        floor = fg.size * (2e-5 if thin else 4e-4)          # drops the Gemini sparkle
        keep = [i + 1 for i, a in enumerate(areas) if a > floor]
        fg = np.isin(lab, keep)
    if not thin:
        fg = ndimage.binary_erosion(fg, iterations=1)
    blur = 0.5 if thin else 0.9
    alpha = np.clip((ndimage.gaussian_filter(fg.astype(float), blur) - .15) / .7, 0, 1)
    spill = np.clip(g - np.maximum(r, b), 0, None)          # pull the green cast off edge pixels
    rgb = im.copy()
    rgb[..., 1] -= spill
    return alpha, rgb


def pad_to(arr, ratio, anchor):
    """pad an RGBA array out to an exact w/h ratio; returns the array and the object's offset"""
    h, w = arr.shape[:2]
    if w / h < ratio:
        W, H = round(h * ratio), h
    else:
        W, H = w, round(w / ratio)
    ox = (W - w) // 2
    oy = {'top': 0, 'bottom': H - h}.get(anchor, (H - h) // 2)
    out = np.zeros((H, W, 4), arr.dtype)
    out[oy:oy + h, ox:ox + w] = arr
    return out, ox, oy, W, H


jobs = {j['name']: j for j in json.load(open('jobs.json'))}
names = sys.argv[1:] or list(jobs)
meta = json.load(open('layers.json')) if os.path.exists('layers.json') else {}
slots = json.load(open('slots.json')) if os.path.exists('slots.json') else {}

for name in names:
    j = jobs.get(name)
    src = f'{SRC}/{name}.png'
    if not j or not os.path.exists(src):
        continue
    fit, bw, bh = j['fit'], j['w'], j['h']

    # ---- full-bleed backgrounds: cover-crop to 1600x900, no keying --------
    if fit == 'bg':
        im = Image.open(src).convert('RGB')
        s = max(1600 / im.width, 900 / im.height)
        im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
        l, t = (im.width - 1600) // 2, (im.height - 900) // 2
        im.crop((l, t, l + 1600, t + 900)).save(f'{IMG}/{name}.webp', 'WEBP', quality=BGQ, method=6)
        print(f'{name:<12} bg     1600x900  {os.path.getsize(f"{IMG}/{name}.webp")//1024} KB')
        continue

    # ---- backdrop plates: cover-crop to the box ratio, no keying ----------
    if fit == 'cover' and j['keys'] == 0:
        im = Image.open(src).convert('RGB')
        s = max(bw / im.width, bh / im.height)
        tw, th = round(im.width * s), round(im.height * s)
        im = im.resize((tw, th), Image.LANCZOS)
        cw, ch = round(bw / bh * th), th
        if cw > tw:
            cw, ch = tw, round(bh / bw * tw)
        l, t = (tw - cw) // 2, (th - ch) // 2
        img = save(im.crop((l, t, l + cw, t + ch)), f'{IMG}/{name}.webp', min(1200, bw * 2), Q)
        meta[name] = {'w': img.width, 'h': img.height}
        print(f'{name:<12} cover  {img.size}  {os.path.getsize(f"{IMG}/{name}.webp")//1024} KB')
        continue

    im = np.asarray(Image.open(src).convert('RGB')).astype(int)
    alpha, rgb = key_green(im, thin=name in THIN)

    # ---- the icons sheet: one render, three cut-outs ----------------------
    if fit == 'sheet':
        parts = blobs(alpha > .5)
        want = j['slices']
        if len(parts) != len(want):
            print(f'{name:<12} SHEET got {len(parts)} blobs, wanted {len(want)} -- check it')
        for part, (x0, y0, x1, y1) in zip(want, parts):
            pj = jobs.get(part) or {}
            a = alpha.copy()
            a[:, :x0] = 0; a[:, x1:] = 0; a[:y0] = 0; a[y1:] = 0      # mask to this blob's column
            sub = np.dstack([rgb, a * 255])[y0:y1, x0:x1].clip(0, 255).astype('uint8')
            tw, th = SHEET_BOX[part]
            out, *_ = pad_to(sub, tw / th, ANCHOR.get(part, 'center'))
            img = save(Image.fromarray(out, 'RGBA'), f'{IMG}/{part}.webp', min(1100, tw * 2), Q)
            meta[part] = {'w': img.width, 'h': img.height}
            print(f'  {part:<10} sheet  {img.size}  {os.path.getsize(f"{IMG}/{part}.webp")//1024} KB')
        continue

    # ---- keys=2: the magenta slots are holes in the host ------------------
    mag = None
    if j['keys'] == 2:
        r, g, b = im[..., 0], im[..., 1], im[..., 2]
        mag = ndimage.binary_opening(np.minimum(r, b) - g > 60, iterations=2)
        alpha = alpha * ~ndimage.binary_dilation(mag, iterations=1)

    ys, xs = np.where(alpha > .02)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    cut = np.dstack([rgb, alpha * 255])[y0:y1, x0:x1].clip(0, 255).astype('uint8')

    if fit == 'cover':                       # wide bands: crop the keyed object to the box ratio
        h, w = cut.shape[:2]
        cw, ch = w, round(w / (bw / bh))
        if ch > h:
            cw, ch = round(h * bw / bh), h
        l = (w - cw) // 2
        t = {'top': 0, 'bottom': h - ch}.get(ANCHOR.get(name, 'center'), (h - ch) // 2)
        cut = cut[t:t + ch, l:l + cw]
        ox = oy = 0; W, H = cw, ch
    else:
        cut, ox, oy, W, H = pad_to(cut, bw / bh, ANCHOR.get(name, 'center'))

    img = save(Image.fromarray(cut, 'RGBA'), f'{IMG}/{name}.webp', min(1100, max(320, bw * 2)), Q)
    meta[name] = {'w': img.width, 'h': img.height}
    print(f'{name:<12} {fit:<6} {img.size}  {os.path.getsize(f"{IMG}/{name}.webp")//1024} KB')

    # ---- report the slots, in design space --------------------------------
    if mag is not None:
        found = blobs(mag)
        want = SLOTS[name]
        print(f'  slots: found {len(found)}, wanted {len(want)}')
        rects = []
        hx, hy = HOST_XY[name]
        for (sx0, sy0, sx1, sy1) in found:
            dx = hx + (ox + sx0 - x0) * bw / W
            dy = hy + (oy + sy0 - y0) * bh / H
            dw = (sx1 - sx0) * bw / W
            dh = (sy1 - sy0) * bh / H
            rects.append([round(dx), round(dy), round(dw), round(dh)])
        for part, rect in zip(want, rects):
            print(f'    {part:<10} {rect}')
        slots[name] = {'want': want, 'rects': rects}

json.dump(meta, open('layers.json', 'w'), indent=1)
json.dump(slots, open('slots.json', 'w'), indent=1)
