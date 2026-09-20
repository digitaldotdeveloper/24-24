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
RECESS = (12, 15, 20)          # what a magenta slot is repainted as


def fix_slots(name, found, want):
    """Gemini does not always return the slots as cleanly as the prompt asks."""
    if name == 'rack' and len(found) > len(want):
        # It draws more slots than asked for (six, not four). The three cells are the tall
        # ones; the BMS is the topmost strip. Any leftover slot stays a dark empty bay,
        # which is what an unpopulated rack looks like anyway.
        tall = sorted(sorted(found, key=lambda b: b[3] - b[1])[-3:], key=lambda b: b[1])
        found = [sorted(found, key=lambda b: b[1])[0]] + tall
    if name == 'house' and len(found) == len(want):
        # one window often comes back a different shape; make all four the median size,
        # kept on the centre each one actually landed on
        ws = sorted(b[2] - b[0] for b in found)
        hs = sorted(b[3] - b[1] for b in found)
        mw, mh = ws[len(ws) // 2], hs[len(hs) // 2]
        cy = [(b[1] + b[3]) // 2 for b in found]
        for i, y in enumerate(cy):                  # snap a row to its median: a window that
            row = [v for v in cy if abs(v - y) < mh]   # came back as a tall balcony door sits
            cy[i] = sorted(row)[len(row) // 2]         # lower, and reads as a mistake
        found = [[(b[0] + b[2]) // 2 - mw // 2, y - mh // 2,
                  (b[0] + b[2]) // 2 + mw // 2, y + mh // 2] for b, y in zip(found, cy)]
    return found


SEG = {'0': 'ABCDEF', '1': 'BC', '2': 'ABGED', '3': 'ABGCD', '4': 'FGBC',
       '5': 'AFGCD', '6': 'AFGEDC', '7': 'ABC', '8': 'ABCDEFG', '9': 'ABCDFG'}
LIT, DIM, BLOOM = (254, 232, 182), (58, 48, 28), (255, 168, 60)


def _seg_polys(x, y, w, h, t, g=None):
    """the seven chamfered bars of a seven-segment digit, keyed A-G"""
    g = round(t * 0.55) if g is None else g
    m, hw = y + h / 2, t / 2
    def hor(cy):
        return [(x + g, cy), (x + hw + g, cy - hw), (x + w - hw - g, cy - hw),
                (x + w - g, cy), (x + w - hw - g, cy + hw), (x + hw + g, cy + hw)]
    def ver(cx, y0, y1):
        return [(cx, y0 + g), (cx + hw, y0 + hw + g), (cx + hw, y1 - hw - g),
                (cx, y1 - g), (cx - hw, y1 - hw - g), (cx - hw, y0 + hw + g)]
    return {'A': hor(y + hw), 'D': hor(y + h - hw), 'G': hor(m),
            'F': ver(x + hw, y, m), 'B': ver(x + w - hw, y, m),
            'E': ver(x + hw, m, y + h), 'C': ver(x + w - hw, m, y + h)}


def draw_lcd(img, text='6.0'):
    """Repaint the inverter's digits. Gemini renders plausible-looking glyphs that are not
    actually numbers, and no prompt fixes that, so the readout is drawn instead. The bar
    graph and the backlit glass it came back with are kept."""
    from PIL import ImageDraw, ImageFilter
    a = np.asarray(img.convert('RGBA')).astype(int)
    lit = (a[..., :3].mean(2) > 150) & (a[..., 3] > 200)
    col = lit.sum(0)
    runs, s = [], None                                   # lit column runs: bars, then digits
    for x, v in enumerate(np.append(col, 0)):
        if v and s is None: s = x
        elif not v and s is not None: runs.append((s, x)); s = None
    runs = [r for r in runs if r[1] - r[0] > 8]
    if len(runs) < 2:
        return img
    x0, x1 = runs[1][0], runs[-1][1]                     # everything right of the bar graph
    ys = np.where(lit[:, x0:x1].any(1))[0]
    y0, y1 = int(ys.min()), int(ys.max())
    h = y1 - y0
    t = max(5, round(h * 0.105))

    # Wipe only the pixels the old glyphs actually lit, refilled with the dark glass around
    # them. A plain rectangle leaves a visible seam: the glass is not one flat colour.
    # The wipe threshold has to be far lower than the detection one. `lit` finds only the
    # cores of the old glyphs; their glow and antialiased edges sit around 60-150 and, left
    # behind, read as extra lit segments -- which is what made the 6 look like an 8.
    reg = (slice(max(0, y0 - 2 * t), y1 + 2 * t), slice(max(0, x0 - 2 * t), x1 + 2 * t))
    patch = a[reg].copy()
    old = ndimage.binary_dilation(patch[..., :3].mean(2) > 55, iterations=max(3, t // 2))
    dark = patch[..., :3][~old]
    patch[..., :3][old] = np.median(dark, axis=0) if len(dark) else (26, 23, 14)
    a[reg] = patch
    base = Image.fromarray(a.clip(0, 255).astype('uint8'), 'RGBA')
    d = ImageDraw.Draw(base)

    glyphs = [c for c in text if c != '.']
    dots = text.count('.')
    gap = round(t * 0.8)
    dw = (x1 - x0 - gap * (len(glyphs) - 1) - dots * (t + gap)) / len(glyphs)
    # lit and unlit go on separate layers: the bloom is built from the LIT one alone, or the
    # dark segments glow too and every digit reads as an 8
    lay = Image.new('RGBA', base.size, (0, 0, 0, 0))
    off = Image.new('RGBA', base.size, (0, 0, 0, 0))
    dl, do = ImageDraw.Draw(lay), ImageDraw.Draw(off)
    cx = x0
    for c in text:
        if c == '.':
            dl.ellipse([cx, y1 - t, cx + t, y1], fill=LIT + (255,))
            cx += t + gap
            continue
        for k, pts in _seg_polys(cx, y0, dw, h, t).items():
            if k in SEG.get(c, ''):
                dl.polygon(pts, fill=LIT + (255,))
            else:
                do.polygon(pts, fill=DIM + (70,))
        cx += dw + gap

    # wide and faint, so it reads as glow rather than thickening the stroke
    bloom = lay.filter(ImageFilter.GaussianBlur(t * 0.85))
    tint = Image.new('RGBA', base.size, BLOOM + (0,))
    tint.putalpha(bloom.split()[3].point(lambda v: int(v * 0.22)))
    base.alpha_composite(off)
    base.alpha_composite(tint)
    base.alpha_composite(lay)
    return base


POST = {'inv_screen': draw_lcd}


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

    # ---- keys=3: a glow, keyed by luminance off black ---------------------
    # A halo that fades into a chroma key cannot be separated from it: the blend goes olive
    # against green and no threshold splits "dim glow" from "background". Rendered on black,
    # brightness IS the alpha, which is exactly how a glow composites anyway.
    if j['keys'] == 3:
        lum = (im[..., 0] * .299 + im[..., 1] * .587 + im[..., 2] * .114) / 255
        alpha = np.clip(lum * 1.25, 0, 1)
        # it draws the core mid-grey however hard the prompt asks for white, which reads as a
        # moon; lift the bright end so the core clips to white and the halo keeps its colour
        rgb = np.clip(im * (1 + 1.1 * lum[..., None]), 0, 255)
    else:
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

    # ---- keys=2: the magenta slots are recesses in the host ---------------
    mag = None
    if j['keys'] == 2:
        r, g, b = im[..., 0], im[..., 1], im[..., 2]
        d = np.minimum(r, b) - g
        mag = ndimage.binary_opening(d > 40, iterations=2)        # slot rects
        # Paint every magenta pixel as a dark recess rather than punching it transparent, so a
        # child that does not quite fill its slot shows shadow and not the page behind. The fill
        # threshold is much looser than the detection one because the slots come back with a
        # soft gradient at the edges, and anything left of it reads as a pink smear.
        # Nothing in these three subjects is legitimately pink, so this cannot eat the object.
        rgb[ndimage.binary_dilation(d > 10, iterations=2)] = RECESS

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
    if name in POST:                      # drawn at final size: no resample blur on the segments
        img = POST[name](img)
        img.save(f'{IMG}/{name}.webp', 'WEBP', quality=Q, method=6, alpha_quality=AQ)
    meta[name] = {'w': img.width, 'h': img.height}
    print(f'{name:<12} {fit:<6} {img.size}  {os.path.getsize(f"{IMG}/{name}.webp")//1024} KB')

    # ---- report the slots, in design space --------------------------------
    if mag is not None:
        found = fix_slots(name, blobs(mag), SLOTS[name])
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
