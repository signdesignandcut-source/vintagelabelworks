# Vintage Label Works - website

A plain HTML site (no build step, no server, no monthly fees). Open `index.html` in a browser to see it.

| Page | What it does |
|---|---|
| `index.html` | Short intro, one tile per category, how it works |
| `category.html?c=<id>` | Grid of before/after pairs for one category; click one for the big view and story |
| `contact.html` | Contact form with photos, emailed to you by FormSubmit |
| `thanks.html` | Shown after a message is sent |

## Editing
- **Name, email, Instagram link:** `assets/js/config.js`
- **Categories and jobs:** `assets/js/data.js`. `CATEGORIES` holds the home page tiles (name, description, cover photo). `GALLERY` has one line per job (category, title, after photo, before photo, story). Photos are in `images/work/`.
- **Look:** `assets/css/style.css`

## Contact form (FormSubmit, free, no account)
1. Put your email in `email` in `config.js` and publish.
2. Send a test message from the Contact page. FormSubmit emails you an **Activate** link. Click it.
3. Every message now arrives in your inbox, with photos attached. Replying goes straight to the customer.
4. Optional, recommended: the activation email includes a random code. Put it in `formId` so your email address isn't visible in the page source.

## Going live on vintagelabelworks.com (Cloudflare Pages, free)
1. Cloudflare dashboard > **Workers & Pages** > **Create** > **Pages** > **Connect to Git** and pick the GitHub repository with this site.
2. Settings: Framework preset **None**. Build command **empty**. Build output directory: the folder holding `index.html` (`/`, the top of this repository).
3. **Save and Deploy.** The site goes live at `<project>.pages.dev`.
4. Project > **Custom domains** > add `vintagelabelworks.com` and `www.vintagelabelworks.com`. Cloudflare sets up DNS and HTTPS by itself, since the domain is in the same account.
5. From now on, every change pushed to the production branch updates the live site within a minute. Other branches get their own preview addresses, which serve as a staging site.

## mattblast.com forwarding to vintagelabelworks.com
1. In the **mattblast.com** zone > **DNS**: add an `A` record, name `@`, IPv4 `192.0.2.1`, Proxy **on** (orange cloud). Add the same with name `www`. This placeholder address is never contacted; Cloudflare answers first.
2. **Rules** > **Redirect Rules** > **Create rule**: "All incoming requests", then "Dynamic" redirect to `concat("https://vintagelabelworks.com", http.request.uri.path)`, status **301**, preserve query string.
