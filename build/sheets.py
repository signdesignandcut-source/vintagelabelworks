# Build posts.json (label posts only) + contact sheets for before/after review.
import re, json, os, sys, textwrap, datetime
from PIL import Image, ImageDraw, ImageFont, ImageOps
IG = sys.argv[1]
rows = [l.rstrip('\n').split('\t') for l in open(f'{IG}/index.tsv', encoding='utf-8')]
kw = re.compile(r'label|decal|sticker|reproduc|nameplate|name plate|badge|data plate|restor|vinyl|emblem|logo|tag\b', re.I)
paths = {}
for root, _, fs in os.walk(f'{IG}/x/posts'):
    for f in fs: paths[f] = os.path.join(root, f)
posts = []
for r in rows:
    cap = r[2] if len(r) > 2 else ''
    if not kw.search(cap): continue
    files = [f for f in r[1].split(',') if f in paths and f.endswith('.jpg')]
    if not files: continue
    posts.append({'id': f'p{len(posts)+1:03d}', 'ts': int(r[0]), 'date': str(datetime.date.fromtimestamp(int(r[0]))), 'files': files, 'caption': cap})
json.dump(posts, open(f'{IG}/posts.json', 'w'), indent=1, ensure_ascii=False)
os.makedirs(f'{IG}/sheets', exist_ok=True)
try: font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 22); small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 15)
except Exception: font = small = ImageFont.load_default()
H = 230; PER = 8
for s in range(0, len(posts), PER):
    chunk = posts[s:s+PER]
    rowsimg = []
    for p in chunk:
        thumbs = []
        for i, f in enumerate(p['files'][:10]):
            im = ImageOps.exif_transpose(Image.open(paths[f])).convert('RGB'); im.thumbnail((400, H))
            c = Image.new('RGB', (im.width, H), 'white'); c.paste(im, (0, 0))
            d = ImageDraw.Draw(c); d.rectangle((0, 0, 34, 30), fill='red'); d.text((7, 2), str(i+1), fill='white', font=font)
            thumbs.append(c)
        w = 330 + sum(t.width + 8 for t in thumbs)
        row = Image.new('RGB', (w, H + 10), '#eeeeee'); d = ImageDraw.Draw(row)
        d.text((8, 6), p['id'], fill='black', font=font)
        d.multiline_text((8, 40), '\n'.join(textwrap.wrap(p['caption'][:260], 38)[:9]), fill='#333', font=small)
        x = 330
        for t in thumbs: row.paste(t, (x, 5)); x += t.width + 8
        rowsimg.append(row)
    W = max(r.width for r in rowsimg); sheet = Image.new('RGB', (W, sum(r.height for r in rowsimg)), 'white'); y = 0
    for r in rowsimg: sheet.paste(r, (0, y)); y += r.height
    sheet.save(f'{IG}/sheets/sheet{s//PER+1:02d}.jpg', quality=80)
print(len(posts), 'posts,', (len(posts)+PER-1)//PER, 'sheets')
