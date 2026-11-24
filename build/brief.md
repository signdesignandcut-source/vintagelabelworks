You are classifying Instagram posts from a label-reproduction business (owner: mattblast) for their website's before/after gallery.

Contact sheets: /tmp/claude-0/-home-user-Design/8577ca64-a58c-565f-9abf-598eea18a22b/scratchpad/ig/sheets/sheetNN.jpg
Each row is one post: post id (p001...) and the start of the caption on the left, then its photos numbered 1, 2, 3... with red tags.
Full captions: /tmp/claude-0/-home-user-Design/8577ca64-a58c-565f-9abf-598eea18a22b/scratchpad/ig/posts.json (fields id, date, files, caption). Read it for the posts on your sheets; captions often say which photo is the original ("top is original", "last photo is of the original").
If a thumbnail is too small to judge, open the full photo: the files listed for the post (in order, photo 1 = files[0]) are somewhere under /tmp/claude-0/-home-user-Design/8577ca64-a58c-565f-9abf-598eea18a22b/scratchpad/ig/x/posts/ (find by filename). Only do that when needed.

For EACH post on your sheets decide:
- after: photo number (1-based) that best shows the NEW reproduction label, ideally installed on the machine, otherwise the cleanest shot of the new label(s).
- before: photo number that best shows the ORIGINAL worn/faded/damaged label (or the machine before). null if no photo shows an original. Never the same as after. If one photo shows old and new side by side, use it as "after" and set before to null, and set "sidebyside": true.
- title: short gallery title, brand + model + what it is, e.g. "Craftsman 397.19340 1/2 HP Grinder Label", "Leiphart Chevrolet Dealer Sticker". Max 60 chars. No @handles.
- note: one plain sentence (max 140 chars) from the caption about what was special (material, how it was rebuilt). No @handles, no hashtags.
- category: one of shop-machinery (grinders, drill presses, lathes, saws, sanders, mills, shears, shapers, planers, jointers, motors for these, dust collectors, buffers, drill sharpeners), automotive (cars, trucks, dealer stickers, air cleaners, engine/fuse/valve cover labels, tires, wheels, jeeps), garage-equipment (compressors, jacks, lifts, chargers, winches, vises, shop cabinets), tools (tool chests/boxes, hand tools, tap & die sets, hammers, drill indexes, power hand tools like Skilsaw/sanders held by hand), farm (tractors, trenchers, implements), marine-outdoor (mowers, small gas engines, chainsaws, outboards), gas-oil (pumps, oil cans), home-vintage (fans, appliances, player pianos, scales, displays, signs, anything else).
- type: machine type, Title Case, short (e.g. "Bench Grinder", "Drill Press", "Dealer Sticker", "Motor", "Lathe", "Greens Mower").
- brand: the machine's maker (e.g. "Craftsman", "Baldor", "Delta", "Rockwell", "Chevrolet"). "" if unclear.
- skip: true only if the post is not label/decal/plate work at all (personal photos). Otherwise false.
- score: 1-5, how impressive the before/after is for a portfolio (5 = dramatic worn original vs. perfect new label, both clearly visible).

Write your results as a JSON array to the output file named in your task, one object per post:
{"id":"p001","after":1,"before":4,"sidebyside":false,"title":"...","note":"...","category":"marine-outdoor","type":"Greens Mower","brand":"Bunton","skip":false,"score":4}
Cover every post on your sheets. Then reply with only: the output path, the number of posts, and how many have before=null.
