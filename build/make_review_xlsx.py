# Review workbook for the Vintage Label Works gallery: one row per job with thumbnails.
#   python3 -I make_review_xlsx.py <ig dir> <site data.js> <out.xlsx>
import json, glob, os, re, sys, io
from PIL import Image, ImageOps
from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation

IG, DATA, OUT = sys.argv[1:4]
posts = {p['id']: p for p in json.load(open(f'{IG}/posts.json', encoding='utf-8'))}
reviews = {}
for f in sorted(glob.glob(f'{IG}/review_*.json')):
    for r in json.load(open(f, encoding='utf-8')): reviews.setdefault(r['id'], r)
js = open(DATA, encoding='utf-8').read()
cats = json.loads('[' + re.search(r'window\.CATEGORIES = \[(.*?)\];', js, re.S).group(1).strip().rstrip(',') + ']')
gal = json.loads('[' + re.search(r'window\.GALLERY = \[(.*?)\];', js, re.S).group(1).strip().rstrip(',') + ']')
catname = {c['id']: c['name'] for c in cats}
order = {c['id']: n for n, c in enumerate(cats)}
paths = {}
for root, _, fs in os.walk(f'{IG}/x/posts'):
    for f in fs: paths[f] = os.path.join(root, f)

TH = 120  # thumbnail height in pixels
def thumb(path, w=150):
    im = ImageOps.exif_transpose(Image.open(path)).convert('RGB')
    im.thumbnail((w, TH))
    buf = io.BytesIO(); im.save(buf, 'JPEG', quality=70); buf.seek(0)
    x = XLImage(buf); x.width, x.height = im.size
    return x

F = 'Arial'
head_font = Font(name=F, bold=True, color='FFFFFF', size=10)
head_fill = PatternFill('solid', fgColor='1B1A17')
edit_fill = PatternFill('solid', fgColor='FFF2B3')
grey_fill = PatternFill('solid', fgColor='EEEEEE')
thin = Side(style='thin', color='BBBBBB')
box = Border(left=thin, right=thin, top=thin, bottom=thin)
wrap = Alignment(wrap_text=True, vertical='center')
center = Alignment(horizontal='center', vertical='center', wrap_text=True)

wb = Workbook()
# ---- How to use ----
hw = wb.active; hw.title = 'How to use'
rows = [
    ('Vintage Label Works - gallery review', True),
    ('', False),
    ('On the "Jobs" sheet, fix anything that is wrong in the YELLOW columns, then send the file back. Leave a yellow cell as it is if it is right.', False),
    ('', False),
    ('Category - pick one from the drop-down (Baldor, Craftsman, Delta, Milwaukee, Rockwell, Porter Cable, Automotive, Other Projects) or type any other name to make a new category.', False),
    ('Title - type the correct name (brand, model, what it is).', False),
    ('Before # / After # - the number of the photo to use, from the "Photo 1, Photo 2..." columns on the right. Leave Before # empty if there is no photo of the original.', False),
    ('Hide - type Y to take the job off the website.', False),
    ('Notes - anything else (e.g. "photo needs rotating", "this is a Delta, not Rockwell").', False),
    ('', False),
    ('The grey columns show what the website uses now, for comparison. Rows are grouped by category.', False),
    ('', False),
    ('Example of a corrected row:', True),
]
for i, (t, b) in enumerate(rows, 1):
    c = hw.cell(row=i, column=1, value=t); c.font = Font(name=F, bold=b, size=14 if i == 1 else 11); c.alignment = Alignment(wrap_text=True)
ex = [('ID', 'p020'), ('Category', 'Other Projects'), ('Title', 'Di-Acro No. 3 Shear Nameplate'), ('Before #', 3), ('After #', 1), ('Hide', ''), ('Notes', 'Before photo was the wrong one')]
for j, (h, v) in enumerate(ex):
    a = hw.cell(row=14, column=1 + j, value=h); a.font = head_font; a.fill = head_fill
    b = hw.cell(row=15, column=1 + j, value=v); b.font = Font(name=F); b.fill = edit_fill if j else grey_fill; b.border = box
hw.column_dimensions['A'].width = 110
for col in 'BCDEFG': hw.column_dimensions[col].width = 24

# ---- Jobs ----
ws = wb.create_sheet('Jobs')
maxp = max(len(posts[g['id']]['files']) for g in gal)
heads = ['ID', 'Category', 'Title', 'Before #', 'After #', 'Hide', 'Notes', 'Before (now)', 'After (now)', 'Instagram caption'] + [f'Photo {i}' for i in range(1, maxp + 1)]
for j, h in enumerate(heads, 1):
    c = ws.cell(row=1, column=j, value=h); c.font = head_font; c.fill = head_fill; c.alignment = center
widths = [7, 24, 34, 9, 9, 7, 26, 22, 22, 40] + [22] * maxp
for j, w in enumerate(widths, 1): ws.column_dimensions[ws.cell(row=1, column=j).column_letter].width = w
ws.freeze_panes = 'D2'

dv = DataValidation(type='list', formula1='"' + ','.join(c['name'] for c in cats) + '"', allow_blank=False,
                    showErrorMessage=False)  # a suggestion list: any category can be typed
ws.add_data_validation(dv)
dvh = DataValidation(type='list', formula1='"Y"', allow_blank=True); ws.add_data_validation(dvh)

gal.sort(key=lambda g: (order[g['group']], g['id']))
for r, g in enumerate(gal, 2):
    p = posts[g['id']]; rv = reviews[g['id']]
    a = rv.get('after') or 1; b = rv.get('before') if g.get('before') else None
    vals = [g['id'], catname[g['group']], g['title'], b, a, '', '', None, None, p['caption'][:300]]
    for j, v in enumerate(vals, 1):
        c = ws.cell(row=r, column=j, value=v); c.font = Font(name=F, size=10); c.border = box
        c.alignment = center if j in (1, 4, 5, 6) else wrap
        c.fill = edit_fill if 2 <= j <= 7 else (grey_fill if j in (1, 8, 9) else PatternFill())
    dv.add(f'B{r}'); dvh.add(f'F{r}')
    ws.row_dimensions[r].height = TH * 0.75 + 8
    ws.add_image(thumb(g['after_src'] if 'after_src' in g else os.path.join(os.path.dirname(DATA), '..', '..', g['after'])), f'I{r}')
    if g.get('before'): ws.add_image(thumb(os.path.join(os.path.dirname(DATA), '..', '..', g['before'])), f'H{r}')
    for k, f in enumerate(p['files']):
        col = ws.cell(row=r, column=11 + k).column_letter
        ws.add_image(thumb(paths[f]), f'{col}{r}')
ws.auto_filter.ref = f'A1:G{len(gal) + 1}'
wb.active = 1
wb.save(OUT)
print(len(gal), 'rows;', maxp, 'photo columns;', round(os.path.getsize(OUT) / 1e6, 1), 'MB')
