# Wires the rendered WebPs into ../index.html:
#   - fills SLIDES[i].images with whatever exists in ../img/ (so it is safe to run part-way)
#   - moves the child layers onto the magenta slots their host actually came back with
# Idempotent: it rewrites from index.src.html, which is the untouched original.
import json, os, re, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
SRC, DST = '../index.src.html', '../index.html'
if not os.path.exists(SRC):
    shutil.copy(DST, SRC)                       # first run: keep the placeholder original
html = open(SRC, encoding='utf-8').read()

# layer id -> the file that fills it, per slide, in SLIDES order
SLIDE_IMAGES = [
    ('blackout', {'bg': 'bg-blackout', 'skyline': 'skyline', 'tower_l': 'tower_l',
                  'tower_r': 'tower_r', 'wires': 'wires', 'bulb': 'bulb', 'meter': 'meter',
                  'moteur': 'moteur', 'candle': 'candle'}),
    ('panels',   {'bg': 'bg-panels', 'sun': 'sun', 'cloud': 'cloud', 'roof': 'roof',
                  'panel_a': 'panel_a', 'panel_b': 'panel_b', 'bracket': 'bracket', 'bird': 'bird'}),
    ('inverter', {'bg': 'bg-inverter', 'wall': 'wall', 'cable_in': 'cable_in',
                  'inv_body': 'inv_body', 'inv_cover': 'inv_cover', 'inv_screen': 'inv_screen',
                  'fan': 'fan', 'bracket_i': 'bracket_i', 'cable_out': 'cable_out'}),
    ('battery',  {'bg': 'bg-battery', 'rack': 'rack', 'bms': 'bms', 'cell3': 'cell',
                  'cell2': 'cell', 'cell1': 'cell', 'led_bar': 'led_bar', 'cable_b': 'cable_b',
                  'breaker': 'breaker'}),
    ('onreal',   {'bg': 'bg-onreal', 'moon': 'moon', 'street': 'street', 'house': 'house',
                  'roof_pv': 'roof_pv', 'win1': 'window', 'win2': 'window', 'win3': 'window',
                  'win4': 'window', 'ac': 'ac', 'wifi': 'wifi', 'fridge': 'fridge'}),
]

# ---- 1. move the children onto the slots their host actually rendered -----
slots = json.load(open('slots.json')) if os.path.exists('slots.json') else {}
moved = {}
for host, d in slots.items():
    for part, rect in zip(d['want'], d['rects']):
        moved[part] = rect

def move(m):
    part = m.group(1)
    if part not in moved:
        return m.group(0)
    x, y, w, h = moved[part]
    return f"L('{part}',{' ' * max(1, 10 - len(part))}{x:>4}, {y:>3}, {w:>4}, {h:>3},"

before = html
html = re.sub(r"L\('(\w+)',\s*(-?\d+),\s*(-?\d+),\s*(\d+),\s*(\d+),", move, html)
print(f'moved {len(moved)} child layers onto detected slots: {", ".join(sorted(moved)) or "none"}')

# ---- 2. fill SLIDES[i].images --------------------------------------------
have = {f[:-5] for f in os.listdir('../img') if f.endswith('.webp')}
blocks = []
for key, mapping in SLIDE_IMAGES:
    pairs = [(lid, f'img/{stem}.webp') for lid, stem in mapping.items() if stem in have]
    if not pairs:
        blocks.append('images:{}')
        continue
    body = ', '.join(f"{lid}:'{p}'" for lid, p in pairs)
    blocks.append('images:{ ' + body + ' }')
    print(f'{key:<9} {len(pairs):>2} images')

it = iter(blocks)
html, n = re.subn(r'images:\{\}', lambda m: next(it), html)
assert n == 5, f'expected 5 images:{{}} slots, replaced {n}'

open(DST, 'w', encoding='utf-8').write(html)
print('wrote', DST, len(html), 'bytes')
