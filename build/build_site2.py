# Vintage Label Works: build gallery data + cropped photos from the reviewed Instagram posts.
#   python3 -I build_site2.py <ig dir> <site dir>
import json, glob, os, re, sys, collections
from PIL import Image, ImageOps, ImageChops, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from clean_photo import clean as cleanup, even_silver, crop_to_subject

IG, SITE = sys.argv[1], sys.argv[2]
posts = {p['id']: p for p in json.load(open(f'{IG}/posts.json', encoding='utf-8'))}
reviews = []
for f in sorted(glob.glob(f'{IG}/review_*.json')): reviews += json.load(open(f, encoding='utf-8'))
paths = {}
for root, _, fs in os.walk(f'{IG}/x/posts'):
    for f in fs: paths[f] = os.path.join(root, f)

GROUPS = [  # id, name, blurb
    ('baldor', 'Baldor', 'Grinder, buffer and motor labels'),
    ('craftsman', 'Craftsman', 'Grinders, drill presses, motors and saws'),
    ('delta', 'Delta', 'Grinders, drill presses, saws and motors'),
    ('milwaukee', 'Milwaukee', 'Milwaukee machines and tools'),
    ('rockwell', 'Rockwell', 'Drill presses, grinders and motors'),
    ('porter-cable', 'Porter Cable', 'Sanders, saws and more'),
    ('automotive', 'Automotive', 'Dealer stickers, engine bay labels and plates'),
    ('other', 'Other Projects', 'Lathes, mowers, vises, motors, pianos and more'),
]
NAME2ID = {n.lower(): i for i, n, _ in GROUPS}
OVERRIDES = {}  # id -> fields corrected by the owner (from the review workbook)
if os.path.exists(f'{IG}/overrides.json'): OVERRIDES = json.load(open(f'{IG}/overrides.json', encoding='utf-8'))
def group(r, o=None):
    o = o or OVERRIDES.get(r['id'], {}).get('category')
    if o: return NAME2ID.get(o.strip().lower(), re.sub(r'[^a-z0-9]+', '-', o.strip().lower()).strip('-'))
    if r.get('category') == 'automotive': return 'automotive'
    t = ((r.get('title') or '') + ' ' + (r.get('brand') or '')).lower()
    if 'porter' in t: return 'porter-cable'
    if 'baldor' in t: return 'baldor'
    if 'craftsman' in t or 'sears' in t: return 'craftsman'
    if (r.get('title') or '').lower().startswith('delta'): return 'delta'
    if 'rockwell' in t: return 'rockwell'
    if 'delta' in t: return 'delta'
    if 'milwaukee' in t: return 'milwaukee'
    return 'other'

def trim(im):
    """Cut away plain borders (the white padding Instagram adds), keeping a small margin."""
    small = im.copy(); small.thumbnail((400, 400))
    sw, sh = small.size
    edge = [small.getpixel((x, 0)) for x in range(sw)] + [small.getpixel((x, sh - 1)) for x in range(sw)] + \
           [small.getpixel((0, y)) for y in range(sh)] + [small.getpixel((sw - 1, y)) for y in range(sh)]
    bg = tuple(sorted(p[i] for p in edge)[len(edge) // 2] for i in range(3))
    if sum(bg) < 3 * 200: return im  # only trim light/white borders, never dark photo backgrounds
    diff = ImageChops.difference(small, Image.new('RGB', small.size, bg)).convert('L').filter(ImageFilter.MedianFilter(5))
    box = diff.point(lambda v: 255 if v > 28 else 0).getbbox()
    if not box: return im
    l, t, r, b = box
    if (r - l) * (b - t) > 0.93 * sw * sh: return im  # nothing worth cutting
    pad = int(0.03 * max(r - l, b - t))
    l, t, r, b = max(0, l - pad), max(0, t - pad), min(sw, r + pad), min(sh, b + pad)
    fx, fy = im.width / sw, im.height / sh
    return im.crop((int(l * fx), int(t * fy), int(r * fx), int(b * fy)))

out = f'{SITE}/images/work'
os.makedirs(out, exist_ok=True)
for f in glob.glob(f'{out}/*.jpg'): os.remove(f)
trimmed = 0
def save(src, dst):
    global trimmed
    im = ImageOps.exif_transpose(Image.open(src)).convert('RGB')
    t = crop_to_subject(trim(im))
    if t.size != im.size: trimmed += 1
    t.thumbnail((900, 900), Image.LANCZOS)
    t = cleanup(even_silver(t))
    t.save(dst, 'JPEG', quality=72, optimize=True, progressive=True)  # no metadata kept

def clean(text):
    text = re.sub(r'#\w+', '', text)
    text = re.sub(r'\s*(for|by|with|from)?\s*@[\w.]+', '', text)
    text = re.sub(r'\s+([.,!?])', r'\1', re.sub(r'\s{2,}', ' ', text)).strip()
    return text[:420].rsplit(' ', 1)[0] + '...' if len(text) > 420 else text

items, seen = [], set()
for r in reviews:
    p = posts.get(r.get('id'))
    if not p or r.get('skip') or r['id'] in seen: continue
    seen.add(r['id']); files = p['files']
    o = OVERRIDES.get(r['id'], {})
    if o.get('hide'): continue
    # One post can be split into several jobs (two different labels in one Instagram post).
    for part in (o.get('split') or [o]):
        jid = r['id'] + part.get('suffix', '')
        a = part.get('after', r.get('after') or 1)
        b = part.get('before', r.get('before') if 'split' not in o else None)
        if not (1 <= a <= len(files)): a = 1
        if b is not None and (not (1 <= b <= len(files)) or b == a): b = None
        save(paths[files[a - 1]], f"{out}/{jid}-new.jpg")
        if b: save(paths[files[b - 1]], f"{out}/{jid}-old.jpg")
        if 'more' in part: extra_n = part['more']
        else: extra_n = [n for n in range(1, len(files) + 1) if n not in (a, b) and n not in part.get('drop', [])]
        more = []
        for n in extra_n:
            save(paths[files[n - 1]], f"{out}/{jid}-{n}.jpg"); more.append(f"images/work/{jid}-{n}.jpg")
        rr = dict(r, id=r['id'], title=part.get('title') or r.get('title'))
        items.append({'id': jid, 'group': group(rr, part.get('category')), 'title': (rr['title'] or 'Reproduction label').strip(),
                      'after': f"images/work/{jid}-new.jpg", 'before': f"images/work/{jid}-old.jpg" if b else None,
                      'story': clean(p['caption']), 'more': more, 'date': p['date'][:7], 'score': int(r.get('score') or 3), 'ts': p['ts']})

# Within a category: jobs with a before photo first (best first), then the rest, newest first.
items.sort(key=lambda i: (i['before'] is None, -i['score'], -i['ts']))
counts = collections.Counter(i['group'] for i in items)
cats = []
extra = [(g, g.replace('-', ' ').title(), '') for g in counts if g not in {x[0] for x in GROUPS}]
for gid, name, blurb in GROUPS + extra:
    if not counts[gid]: continue
    best = next((i for i in items if i['group'] == gid and i['before']), None) or next(i for i in items if i['group'] == gid)
    cats.append({'id': gid, 'name': name, 'blurb': blurb, 'image': best['after'], 'count': counts[gid]})
for i in items:
    i.pop('score'); i.pop('ts')
    if not i['before']: i.pop('before')
    if not i['more']: i.pop('more')

head = ('/* Built from the @mattblast Instagram posts. Edit freely:\n'
        '   CATEGORIES: name, blurb and cover image of each tile on the home page (order = order on the page).\n'
        '   GALLERY: one line per job. "group" = category id, "after" = new label, "before" = original.\n'
        '   Photos are in images/work/. Order within a category = order in this list. */\n')
js = head + 'window.CATEGORIES = [\n' + '\n'.join('  ' + json.dumps(c, ensure_ascii=False) + ',' for c in cats) + '\n];\n\n' + \
     'window.GALLERY = [\n' + '\n'.join('  ' + json.dumps(i, ensure_ascii=False) + ',' for i in items) + '\n];\n'
open(f'{SITE}/assets/js/data.js', 'w', encoding='utf-8').write(js)
print(len(items), 'jobs;', trimmed, 'photos cropped;', dict(counts))
print('MB:', round(sum(os.path.getsize(f) for f in glob.glob(f'{out}/*.jpg')) / 1e6, 1))
