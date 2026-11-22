/* Shared by every page: header, footer, and the big before/after view. */
(function () {
  const S = window.SITE;
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  // Logo: a riveted nameplate with VLW.
  const logo = `<svg viewBox="0 0 66 50" aria-hidden="true">
    <rect x="2" y="3" width="62" height="44" rx="6" fill="#b8231b" stroke="#1b1a17" stroke-width="3"/>
    <rect x="8" y="9" width="50" height="32" rx="2.5" fill="none" stroke="#f3ecdc" stroke-width="1.8"/>
    <g fill="#c9962b"><circle cx="8" cy="9" r="2.4"/><circle cx="58" cy="9" r="2.4"/><circle cx="8" cy="41" r="2.4"/><circle cx="58" cy="41" r="2.4"/></g>
    <text x="33" y="32.5" text-anchor="middle" font-family="Oswald, Impact, sans-serif" font-weight="700" font-size="18" letter-spacing="1" fill="#f3ecdc">VLW</text>
  </svg>`;
  const brand = `<a class="brand" href="index.html">${logo}<span><b>${esc(S.name)}</b><small>${esc(S.byline)}</small></span></a>`;

  const page = document.body.dataset.page;
  const header = document.createElement("header");
  header.className = "site-header";
  header.innerHTML = `<div class="wrap nav">${brand}
    <nav class="nav-links"><a href="index.html" class="${page === "home" ? "active" : ""}">Work</a><a href="contact.html" class="${page === "contact" ? "active" : ""}">Contact</a></nav></div>`;
  document.body.prepend(header);

  const footer = document.createElement("footer");
  footer.className = "site-footer";
  footer.innerHTML = `<div class="wrap foot">${brand}
    <span>Reproduction labels, decals and nameplates for restorations &middot; <a href="contact.html">Contact</a> &middot; <a href="${esc(S.instagram)}" target="_blank" rel="noopener">Instagram @mattblast</a> &middot; <a href="${esc(S.garageJournal)}" target="_blank" rel="noopener">GarageJournal thread</a></span>
    <span>&copy; ${new Date().getFullYear()} ${esc(S.name)}. Trademarks belong to their owners.</span></div>`;
  document.body.append(footer);

  // Big view: new and original side by side, with the story and a "ask about this" button.
  function shots(g) {
    const extra = g.more && g.more.length ? `<span class="more-badge">+${g.more.length} photo${g.more.length > 1 ? "s" : ""}</span>` : "";
    return extra + (g.before
      ? `<div class="shots"><div class="shot"><img src="${esc(g.before)}" alt="${esc(g.title)} - original" loading="lazy"><span>Before</span></div><div class="shot new"><img src="${esc(g.after)}" alt="${esc(g.title)} - reproduction" loading="lazy"><span>After</span></div></div>`
      : `<div class="shots one"><div class="shot new"><img src="${esc(g.after)}" alt="${esc(g.title)}" loading="lazy"><span>New</span></div></div>`);
  }
  let lb;
  function open(g) {
    if (!lb) {
      lb = document.createElement("div");
      lb.className = "lightbox"; lb.setAttribute("role", "dialog"); lb.setAttribute("aria-modal", "true");
      lb.innerHTML = `<button class="x" aria-label="Close">&times;</button><div class="inner"></div>`;
      lb.addEventListener("click", (e) => {
        if (e.target === lb || e.target.closest(".x")) return close();
        if (e.target.closest("[data-copy]")) copyLink();
        const t = e.target.closest("[data-more]");
        if (t) lb.querySelector("#more-" + t.dataset.more).scrollIntoView({ behavior: "smooth", block: "start" });
      });
      document.addEventListener("keydown", (e) => e.key === "Escape" && close());
      document.body.append(lb);
    }
    const fig = (src, cap) => `<figure><img src="${esc(src)}" alt="${esc(g.title)} - ${cap}"><figcaption>${cap}</figcaption></figure>`;
    lb.querySelector(".inner").innerHTML = `<div class="big ${g.before ? "" : "one"}">${g.before ? fig(g.before, "Before") : ""}${fig(g.after, g.before ? "After" : "Reproduction")}</div>
      ${g.more && g.more.length ? `<div class="strip"><span>${g.more.length} more photo${g.more.length > 1 ? "s" : ""}:</span>${g.more.map((m, k) => `<button data-more="${k}" aria-label="Show photo ${k + 1}"><img src="${esc(m)}" alt=""></button>`).join("")}</div>` : ""}
      <h3>${esc(g.title)}</h3><p>${esc(g.story || "")}</p>
      <div class="btns"><button class="btn ghost light" data-copy>Copy link</button><span class="copied" hidden>Link copied</span></div>
      ${g.more && g.more.length ? `<h4 class="more-head">More photos</h4><div class="more-photos">${g.more.map((m, k) => `<img id="more-${k}" src="${esc(m)}" alt="${esc(g.title)} - photo ${k + 1}" loading="lazy">`).join("")}</div>` : ""}
      <a class="btn red" href="contact.html?about=${encodeURIComponent(g.title)}">Ask about this label</a>`;
    lb.classList.add("open"); document.body.style.overflow = "hidden"; lb.scrollTop = 0;
    const u = new URL(location.href); u.searchParams.set("job", g.id); history.replaceState(null, "", u);
    lb.querySelector(".x").focus();
  }
  function close() {
    if (!lb) return;
    lb.classList.remove("open"); document.body.style.overflow = "";
    const u = new URL(location.href); u.searchParams.delete("job"); history.replaceState(null, "", u);
  }
  async function copyLink() {
    const done = lb.querySelector(".copied");
    try { await navigator.clipboard.writeText(location.href); done.textContent = "Link copied"; }
    catch { done.textContent = location.href; }  // no clipboard access: show the link to copy by hand
    done.hidden = false;
  }

  window.VLW = { esc, shots, open };
})();
