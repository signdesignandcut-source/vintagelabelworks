# Vintage Label Works - photo build

Turns the @mattblast Instagram export into the site's photos and `assets/js/data.js`
(live site: repository signdesignandcut-source/vintagelabelworks).

- `posts.json` - label posts from the export: id, date, photo files, caption
- `review_*.json` - per post: which photo is "after"/"before", title, category, score
- `overrides.json` - the owner's corrections (category, title, before/after, hide, drop, split into several jobs)
- `build_site2.py <ig dir> <site dir>` - crops, cleans and resizes the photos, writes data.js
- `clean_photo.py` - crop to the label, even lighting on silver, white balance, contrast
- `make_review_xlsx.py` - the review workbook with thumbnails

The ig dir needs these files plus the export's photos unzipped in `x/posts/` (posts.zip from the owner's Google Drive).
