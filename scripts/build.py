#!/usr/bin/env python3
"""
Kobalt Construction site builder.

Reads data/projects.json and data/blog.json (edited via Decap CMS at /admin)
and regenerates:
  - Every individual project detail page (<slug>.html)
  - projects.html (the full gallery grid)
  - Every individual blog post page (<slug>.html)
  - blog.html (the blog grid)

The homepage (index.html), services pages, careers pages, and every other
hand-authored page are left untouched by this script. Only the two content
types Decap CMS manages get regenerated, so this is safe to run on every
commit.

Run from the repo root:  python3 scripts/build.py
"""
import json
import os
import re
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# "Latest From the Field" homepage strip (see build_home_updates).
UPDATE_WINDOW_DAYS = 90   # an update drops off the homepage this many days after its date
HOME_UPDATES_MAX = 3      # most updates shown on the homepage at once


def read_header_footer(from_page="hilltop-heights.html"):
    """Pull the current shared <header> and <footer> markup from an existing
    hand-authored page, so generated pages always match whatever nav/footer
    edits have been made elsewhere on the site."""
    src = (ROOT / from_page).read_text()
    header = re.search(r"(<header>.*?</header>)", src, re.DOTALL).group(1)
    footer = re.search(r"(<footer>.*?</footer>)", src, re.DOTALL).group(1)
    return header, footer


def header_for(header, active_label):
    """Return a copy of the shared header with class="active" moved onto the
    correct nav link (Projects for project pages, Blog for blog pages)."""
    stripped = re.sub(r'(<a href="[^"]+\.html")\s+class="active"(>)', r"\1\2", header)
    return re.sub(
        rf'<a href="([^"]+\.html)">({active_label})<',
        rf'<a href="\1" class="active">\2<',
        stripped
    )


PROJECT_DOC = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-9406J8G3G0"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-9406J8G3G0');
</script>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{seo_title}</title>
<meta name="description" content="{meta_desc}">
<link rel="canonical" href="https://kobaltconstruction.com/{slug}.html">
<link rel="icon" type="image/png" sizes="32x32" href="/images/favicon-32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/images/favicon-16.png">
<link rel="apple-touch-icon" sizes="180x180" href="/images/favicon-180.png">
<meta property="og:type" content="website">
<meta property="og:title" content="{seo_title}">
<meta property="og:description" content="{meta_desc}">
<meta property="og:url" content="https://kobaltconstruction.com/{slug}.html">
<meta property="og:image" content="https://kobaltconstruction.com/{meta_image}">
<meta property="og:site_name" content="Kobalt Construction">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{seo_title}">
<meta name="twitter:description" content="{meta_desc}">
<meta name="twitter:image" content="https://kobaltconstruction.com/{meta_image}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@400;500;600;700&family=Source+Sans+3:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="css/style.css">
</head>
<body>

{header}

<section class="about-hero" style="padding-bottom:130px;">
  <svg class="contours" viewBox="0 0 1180 300" preserveAspectRatio="none">
    <path d="M-50 260 Q 250 180 450 240 T 1230 250" fill="none" stroke="white" stroke-width="2"/>
    <path d="M-50 180 Q 270 100 470 160 T 1230 170" fill="none" stroke="white" stroke-width="2"/>
  </svg>
  <div class="wrap">
    <div class="eyebrow">{tag} Project — {location}</div>
    <h1>{name}</h1>
  </div>
</section>

<section class="project-detail-body" style="padding-top:0;">
  <div class="wrap" style="max-width:800px;">
    {hero_block}
    {source_note}
    {paragraphs}{updates_block}
    {team_block}
    {gallery_block}
    {related_block}
  </div>
</section>

<section class="cta-banner">
  <h2>Have a Project in Mind?</h2>
  <p>Tell us about it and we'll get back to you within one business day.</p>
  <a href="contact.html" class="btn btn-amber">Get a Quote</a>
</section>

{footer}

<script>
(function(){{
  // Scroll-reveal animation for sections (skips the first section to avoid hero flicker)
  var sections = document.querySelectorAll('section');
  if (sections.length > 1 && 'IntersectionObserver' in window) {{
    var revealObserver = new IntersectionObserver(function(entries){{
      entries.forEach(function(entry){{
        if (entry.isIntersecting) {{
          entry.target.classList.add('revealed');
          revealObserver.unobserve(entry.target);
        }}
      }});
    }}, {{ threshold: 0.12 }});
    sections.forEach(function(sec, i){{
      if (i === 0) return;
      sec.classList.add('reveal-section');
      revealObserver.observe(sec);
    }});
  }}

  // Photo gallery lightbox
  var galleryImgs = document.querySelectorAll('.project-gallery img');
  if (galleryImgs.length) {{
    var images = Array.prototype.map.call(galleryImgs, function(img){{ return {{ src: img.src, alt: img.alt }}; }});
    var current = 0;

    var lb = document.createElement('div');
    lb.className = 'kobalt-lightbox';
    lb.setAttribute('role', 'dialog');
    lb.setAttribute('aria-modal', 'true');
    lb.innerHTML =
      '<button class="kobalt-lightbox-close" aria-label="Close">&times;</button>' +
      '<button class="kobalt-lightbox-nav kobalt-lightbox-prev" aria-label="Previous photo">&#8249;</button>' +
      '<img alt="">' +
      '<button class="kobalt-lightbox-nav kobalt-lightbox-next" aria-label="Next photo">&#8250;</button>' +
      '<div class="kobalt-lightbox-count"></div>';
    document.body.appendChild(lb);

    var lbImg = lb.querySelector('img');
    var lbCount = lb.querySelector('.kobalt-lightbox-count');

    function show(i){{
      current = (i + images.length) % images.length;
      lbImg.src = images[current].src;
      lbImg.alt = images[current].alt;
      lbCount.textContent = (current + 1) + ' / ' + images.length;
    }}
    function openLightbox(i){{
      show(i);
      lb.classList.add('open');
      document.body.style.overflow = 'hidden';
    }}
    function closeLightbox(){{
      lb.classList.remove('open');
      document.body.style.overflow = '';
    }}

    galleryImgs.forEach(function(img, i){{
      img.addEventListener('click', function(){{ openLightbox(i); }});
    }});
    lb.querySelector('.kobalt-lightbox-close').addEventListener('click', closeLightbox);
    lb.querySelector('.kobalt-lightbox-prev').addEventListener('click', function(){{ show(current - 1); }});
    lb.querySelector('.kobalt-lightbox-next').addEventListener('click', function(){{ show(current + 1); }});
    lb.addEventListener('click', function(e){{ if (e.target === lb) closeLightbox(); }});
    document.addEventListener('keydown', function(e){{
      if (!lb.classList.contains('open')) return;
      if (e.key === 'Escape') closeLightbox();
      if (e.key === 'ArrowLeft') show(current - 1);
      if (e.key === 'ArrowRight') show(current + 1);
    }});
  }}
}})();
</script>

</body>
</html>
'''

BLOG_DOC = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-9406J8G3G0"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-9406J8G3G0');
</script>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{seo_title}</title>
<meta name="description" content="{meta_desc}">
<link rel="canonical" href="https://kobaltconstruction.com/{slug}.html">
<link rel="icon" type="image/png" sizes="32x32" href="/images/favicon-32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/images/favicon-16.png">
<link rel="apple-touch-icon" sizes="180x180" href="/images/favicon-180.png">
<meta property="og:type" content="article">
<meta property="og:title" content="{seo_title}">
<meta property="og:description" content="{meta_desc}">
<meta property="og:url" content="https://kobaltconstruction.com/{slug}.html">
<meta property="og:image" content="https://kobaltconstruction.com/images/og-share.jpg">
<meta property="og:site_name" content="Kobalt Construction">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{seo_title}">
<meta name="twitter:description" content="{meta_desc}">
<meta name="twitter:image" content="https://kobaltconstruction.com/images/og-share.jpg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@400;500;600;700&family=Source+Sans+3:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="css/style.css">
</head>
<body>

{header}

<section class="about-hero">
  <svg class="contours" viewBox="0 0 1180 300" preserveAspectRatio="none">
    <path d="M-50 260 Q 250 180 450 240 T 1230 250" fill="none" stroke="white" stroke-width="2"/>
    <path d="M-50 180 Q 270 100 470 160 T 1230 170" fill="none" stroke="white" stroke-width="2"/>
  </svg>
  <div class="wrap">
    <div class="eyebrow">{category}</div>
    <h1 style="font-size:32px;">{title}</h1>
  </div>
</section>

<section class="project-detail-body" style="padding-top:56px;">
  <div class="wrap" style="max-width:760px;">
    {paragraphs}
    {source_block}
    {related_line}
  </div>
</section>

<section class="cta-banner">
  <h2>Have a Project in Mind?</h2>
  <p>Tell us about it and we'll get back to you within one business day.</p>
  <a href="contact.html" class="btn btn-amber">Get a Quote</a>
</section>

{footer}

<script>
(function(){{
  // Scroll-reveal animation for sections (skips the first section to avoid hero flicker)
  var sections = document.querySelectorAll('section');
  if (sections.length > 1 && 'IntersectionObserver' in window) {{
    var revealObserver = new IntersectionObserver(function(entries){{
      entries.forEach(function(entry){{
        if (entry.isIntersecting) {{
          entry.target.classList.add('revealed');
          revealObserver.unobserve(entry.target);
        }}
      }});
    }}, {{ threshold: 0.12 }});
    sections.forEach(function(sec, i){{
      if (i === 0) return;
      sec.classList.add('reveal-section');
      revealObserver.observe(sec);
    }});
  }}

  // Photo gallery lightbox
  var galleryImgs = document.querySelectorAll('.project-gallery img');
  if (galleryImgs.length) {{
    var images = Array.prototype.map.call(galleryImgs, function(img){{ return {{ src: img.src, alt: img.alt }}; }});
    var current = 0;

    var lb = document.createElement('div');
    lb.className = 'kobalt-lightbox';
    lb.setAttribute('role', 'dialog');
    lb.setAttribute('aria-modal', 'true');
    lb.innerHTML =
      '<button class="kobalt-lightbox-close" aria-label="Close">&times;</button>' +
      '<button class="kobalt-lightbox-nav kobalt-lightbox-prev" aria-label="Previous photo">&#8249;</button>' +
      '<img alt="">' +
      '<button class="kobalt-lightbox-nav kobalt-lightbox-next" aria-label="Next photo">&#8250;</button>' +
      '<div class="kobalt-lightbox-count"></div>';
    document.body.appendChild(lb);

    var lbImg = lb.querySelector('img');
    var lbCount = lb.querySelector('.kobalt-lightbox-count');

    function show(i){{
      current = (i + images.length) % images.length;
      lbImg.src = images[current].src;
      lbImg.alt = images[current].alt;
      lbCount.textContent = (current + 1) + ' / ' + images.length;
    }}
    function openLightbox(i){{
      show(i);
      lb.classList.add('open');
      document.body.style.overflow = 'hidden';
    }}
    function closeLightbox(){{
      lb.classList.remove('open');
      document.body.style.overflow = '';
    }}

    galleryImgs.forEach(function(img, i){{
      img.addEventListener('click', function(){{ openLightbox(i); }});
    }});
    lb.querySelector('.kobalt-lightbox-close').addEventListener('click', closeLightbox);
    lb.querySelector('.kobalt-lightbox-prev').addEventListener('click', function(){{ show(current - 1); }});
    lb.querySelector('.kobalt-lightbox-next').addEventListener('click', function(){{ show(current + 1); }});
    lb.addEventListener('click', function(e){{ if (e.target === lb) closeLightbox(); }});
    document.addEventListener('keydown', function(e){{
      if (!lb.classList.contains('open')) return;
      if (e.key === 'Escape') closeLightbox();
      if (e.key === 'ArrowLeft') show(current - 1);
      if (e.key === 'ArrowRight') show(current + 1);
    }});
  }}
}})();
</script>

</body>
</html>
'''


import html as _html


def _esc(text):
    """Escape plain text for HTML (idempotent: handles values already containing entities)."""
    return _html.escape(_html.unescape(text), quote=False)


def _attr(text):
    return _esc(text).replace('"', "&quot;")


def short_name(name):
    """'Jeter Avenue | Bethlehem, PA' / 'Wawa — Plains Township' -> first part only."""
    return re.split(r"\s+[|\u2014]\s+", name)[0].strip()


def city_of(location):
    """'800 McKinley St, Hazleton, PA 18202' -> 'Hazleton, PA'; 'Luzerne, PA 18709' -> 'Luzerne, PA'."""
    parts = [x.strip() for x in location.split(",")]
    if parts and re.match(r"^\d", parts[0]):
        parts = parts[1:]
    return re.sub(r"\s+\d{5}(-\d{4})?$", "", ", ".join(parts))


def seo_title_for(name, location, suffix="Kobalt Construction"):
    """Project page <title>, kept to ~65 characters."""
    short, city = short_name(name), city_of(location)
    for candidate in (f"{short} \u2014 {city} | {suffix}", f"{short} | {suffix}"):
        if len(candidate) <= 65:
            return _esc(candidate)
    return _esc(f"{short} | {suffix}")


def seo_desc_for(p):
    """Meta description: an explicit one wins; otherwise expand short card summaries."""
    if p.get("meta_description"):
        return _attr(p["meta_description"])
    summary = (p.get("summary") or "").strip()
    if len(summary) >= 70:
        return _attr(summary)
    short, city = short_name(p["name"]), city_of(p["location"])
    base = f"{short} in {city}: {summary.rstrip('.')}." if summary else f"{short} in {city}."
    full = f"{base} A {p['tag'].lower()} project completed by Kobalt Construction."
    return _attr(full if len(full) <= 158 else base)


SERVICE_PAGE_FOR_TAG = {
    "Public": ("public.html", "public construction services"),
    "Commercial": ("commercial.html", "commercial construction services"),
    "Residential": ("residential.html", "residential construction services"),
}
CAPABILITY_LINKS = {"sitework": ("site-work.html", "Site Work"), "concrete": ("concrete.html", "Concrete"), "paving": ("paving.html", "Paving")}


def related_block_for(p, projects):
    """Contextual internal links: the matching service page, same-category projects, capability pages."""
    mine = set(p.get("capabilities", []))
    same = [q for q in projects if q["slug"] != p["slug"] and q["tag"] == p["tag"]]
    same.sort(key=lambda q: (0 if mine & set(q.get("capabilities", [])) else 1,
                             abs(q.get("order", 999) - p.get("order", 999))))
    svc_href, svc_text = SERVICE_PAGE_FOR_TAG.get(p["tag"], ("services.html", "services"))
    rows = [f'<p>This project is part of our <a href="{svc_href}">{svc_text}</a>.</p>']
    if mine:
        links = " &middot; ".join(f'<a href="{CAPABILITY_LINKS[c][0]}">{CAPABILITY_LINKS[c][1]}</a>' for c in ("sitework", "concrete", "paving") if c in mine)
        rows.append(f"<p>More of our work like this: {links}</p>")
    area = area_for(p["slug"])
    if area:
        rows.append(f'<p>More of our work in <a href="{area[0]}">{area[1]}</a>.</p>')
    if same[:3]:
        links = " &middot; ".join(f'<a href="{q["slug"]}.html">{_esc(short_name(q["name"]))}</a>' for q in same[:3])
        rows.append(f'<p>More {p["tag"].lower()} projects: {links}</p>')
    return '<div class="related-work"><h3>Related</h3>' + "".join(rows) + "</div>"


def blog_seo_title(title):
    for suffix in ("Kobalt Construction Blog", "Kobalt Blog"):
        candidate = f"{title} | {suffix}"
        if len(candidate) <= 65:
            return _esc(candidate)
    return _esc(f"{title} | Kobalt Blog")


def read_shared_blocks(from_page="faq.html"):
    """Pull the shared analytics snippet and end-of-page script from an existing page."""
    text = (ROOT / from_page).read_text()
    ga = re.search(r"(<!-- Google tag \(gtag\.js\) -->.*?gtag\('config'[^\n]*\n</script>)", text, re.DOTALL)
    end = re.search(r"(<script>\n\(function\(\)\{\n  // Scroll-reveal.*?\n\}\)\(\);\n</script>)", text, re.DOTALL)
    if not ga or not end:
        raise SystemExit(f"Could not find the shared analytics / end-of-page script blocks in {from_page}")
    return ga.group(1), end.group(1)


_AREA_MAP = None


def area_for(slug):
    """Which area page (if any) lists this project: returns (page, label)."""
    global _AREA_MAP
    if _AREA_MAP is None:
        _AREA_MAP = {}
        folder = ROOT / "data/areas"
        for path in sorted(folder.glob("*.json")) if folder.exists() else []:
            a = json.loads(path.read_text())
            for pslug in a["projects"]:
                _AREA_MAP.setdefault(pslug, (f"{a['slug']}.html", a["label"]))
    return _AREA_MAP.get(slug)


def extract_areas_map(map_id, height, intro_text):
    """Reuse the proven homepage map block (live OpenStreetMap + MapTiler) for the Projects page,
    so there is one source of truth and a rebuild can never drop it."""
    src = (ROOT / "index.html").read_text()
    m = re.search(r'(<section style="padding-bottom:20px;">.*?)(?=<section id="projects">)', src, re.DOTALL)
    if not m:
        raise SystemExit("Could not find the Areas Served map block in index.html")
    block = m.group(1).replace("areas-leaflet-map-home", map_id).replace("height:380px", f"height:{height}")
    block, n = re.subn(r"(<div class=\"section-head\".*?<p>).*?(</p>)", lambda mm: mm.group(1) + intro_text + mm.group(2), block, count=1, flags=re.DOTALL)
    if n != 1:
        raise SystemExit("Could not adapt the Areas Served intro text")
    return block


def load_folder(folder):
    """Load every *.json file in a data folder, sorted by an explicit
    'order' field if present (Decap CMS folder collections don't guarantee
    file order, so we control display order via this field instead)."""
    items = []
    for path in sorted((ROOT / folder).glob("*.json")):
        item = json.loads(path.read_text())
        # Photo fields are plain filenames ("weis-hero.jpg"). Decap CMS saves them as
        # "images/weis-hero.jpg" or "/images/weis-hero.jpg", so accept either form.
        if isinstance(item.get("hero_image"), str):
            item["hero_image"] = _photo_name(item["hero_image"])
        for g in item.get("gallery") or []:
            if isinstance(g, dict) and isinstance(g.get("image"), str):
                g["image"] = _photo_name(g["image"])
        for u in item.get("updates") or []:
            for g in (u.get("photos") or []) if isinstance(u, dict) else []:
                if isinstance(g, dict) and isinstance(g.get("image"), str):
                    g["image"] = _photo_name(g["image"])
        items.append(item)
    items.sort(key=lambda x: x.get("order", 999))
    return items


def _photo_name(value):
    value = value.strip()
    for prefix in ("/images/", "images/"):
        if value.startswith(prefix):
            return value[len(prefix):]
    return value


def build_date():
    """Today's date, or KOBALT_BUILD_DATE=YYYY-MM-DD to preview the site as of another day."""
    override = os.environ.get("KOBALT_BUILD_DATE")
    return date.fromisoformat(override) if override else date.today()


def updates_of(p):
    """A project's dated updates, newest first, with the date parsed.
    Each update in data/projects/<slug>.json looks like:
      {"date": "2026-10-19", "headline": "One line", "text": ["Paragraph", ...],
       "photos": [{"image": "file.jpg", "alt": "Description"}]}"""
    out = []
    for u in p.get("updates") or []:
        try:
            d = date.fromisoformat(str(u.get("date", "")).strip()[:10])
        except ValueError:
            raise SystemExit(f'data/projects/{p["slug"]}.json: update date "{u.get("date")}" must look like 2026-10-19')
        out.append(dict(u, _date=d))
    out.sort(key=lambda u: u["_date"], reverse=True)
    return out


def nice_date(d, short=False):
    return f'{d.strftime("%b" if short else "%B")} {d.day}, {d.year}'


def updates_block_for(p):
    ups = updates_of(p)
    if not ups:
        return ""
    items = []
    for u in ups:
        d = u["_date"]
        paras = "\n      ".join(f"<p>{para}</p>" for para in u.get("text") or [])
        photos = ""
        if u.get("photos"):
            imgs = "\n        ".join(f'<img src="images/{g["image"]}" alt="{_attr(g.get("alt", ""))}">' for g in u["photos"])
            photos = f'\n      <div class="project-gallery">\n        {imgs}\n      </div>'
        items.append(f'''    <article class="project-update" id="update-{d.isoformat()}">
      <div class="project-update-date"><time datetime="{d.isoformat()}">{nice_date(d)}</time></div>
      <h3>{_esc(u.get("headline", ""))}</h3>
      {paras}{photos}
    </article>''')
    return ('\n    <div class="project-updates" id="updates">\n'
            '    <h2 class="project-updates-title">Project Updates</h2>\n'
            + "\n".join(items) + "\n    </div>")


HOME_START = "<!-- latest-updates:start"
HOME_END = "<!-- latest-updates:end -->"


def build_home_updates():
    """Fill the "Latest From the Field" strip on index.html (between the latest-updates
    markers) with the newest project updates from the last UPDATE_WINDOW_DAYS days.
    A small script in the strip also hides entries once they pass the window, so the
    strip disappears on time even if nobody rebuilds the site."""
    page = ROOT / "index.html"
    text = page.read_text()
    if HOME_START not in text or HOME_END not in text:
        print("  home updates: markers missing from index.html, skipped")
        return
    today = build_date()
    recent = []
    for p in load_folder("data/projects"):
        ups = updates_of(p)
        for u in ups:
            age = (today - u["_date"]).days
            if 0 <= age <= UPDATE_WINDOW_DAYS:
                recent.append((u["_date"], p, u))
    recent.sort(key=lambda r: r[0], reverse=True)
    recent = recent[:HOME_UPDATES_MAX]

    if recent:
        items = []
        for d, p, u in recent:
            thumb = ""
            if u.get("photos"):
                g = u["photos"][0]
                thumb = f'<img class="latest-thumb" src="images/{g["image"]}" alt="">'
            items.append(f'''      <li class="latest-item" data-update-date="{d.isoformat()}">
        <a href="{p["slug"]}.html#update-{d.isoformat()}">{thumb}<span class="latest-text"><span class="latest-meta"><time datetime="{d.isoformat()}">{nice_date(d, short=True)}</time> &middot; {_esc(p["name"].split(" | ")[0].strip())}</span><span class="latest-headline">{_esc(u.get("headline", ""))}</span><span class="latest-cta">Read the update &raquo;</span></span></a>
      </li>''')
        body = f'''
<section class="latest-updates" aria-labelledby="latest-updates-title">
  <div class="wrap">
    <h2 class="eyebrow" id="latest-updates-title">Latest From the Field</h2>
    <ul class="latest-list">
{chr(10).join(items)}
    </ul>
  </div>
</section>
<script>
// Hide updates older than {UPDATE_WINDOW_DAYS} days, even if the site hasn't been rebuilt since.
(function(){{
  var s = document.querySelector('.latest-updates'); if (!s) return;
  var left = 0, max = ({UPDATE_WINDOW_DAYS} + 1) * 864e5;  // through the end of day {UPDATE_WINDOW_DAYS}, same as the build
  s.querySelectorAll('[data-update-date]').forEach(function(li){{
    var t = Date.parse(li.getAttribute('data-update-date') + 'T00:00:00');
    if (isNaN(t) || Date.now() - t > max) li.remove(); else left++;
  }});
  if (!left) s.remove();
}})();
</script>
'''
    else:
        body = "\n"
    start = text.index(HOME_START)
    start_line_end = text.index("-->", start) + 3
    end = text.index(HOME_END)
    text = text[:start_line_end] + body + text[end:]
    page.write_text(text)
    print(f"  home updates: {len(recent)} shown (window {UPDATE_WINDOW_DAYS} days, as of {today.isoformat()})")


CAROUSEL_START = "<!-- carousel:start"
CAROUSEL_END = "<!-- carousel:end -->"


def build_carousel():
    """Build the "Fresh Off the Job Site" 3D carousel on index.html from every project
    with a "carousel" entry: {"order": 1, "label": "Short card label",
    "image": "optional.jpg", "alt": "optional"}. Card photo: the carousel "image" if
    given, otherwise the first photo of the project's newest update, otherwise the hero.
    The ring's spacing is worked out from the number of cards, so cards can be added
    or removed without touching the CSS."""
    import math
    page = ROOT / "index.html"
    text = page.read_text()
    if CAROUSEL_START not in text or CAROUSEL_END not in text:
        print("  carousel: markers missing from index.html, skipped")
        return
    cards = []
    for p in load_folder("data/projects"):
        c = p.get("carousel")
        if not isinstance(c, dict) or not str(c.get("label", "")).strip():
            continue
        if c.get("image"):
            img, alt = _photo_name(c["image"]), c.get("alt") or p.get("hero_alt", "")
        else:
            newest = next((u["photos"][0] for u in updates_of(p) if u.get("photos")), None)
            img, alt = (newest["image"], newest.get("alt", "")) if newest else (p["hero_image"], p.get("hero_alt", ""))
        cards.append((c.get("order", 999), p["slug"], img, alt, c["label"].strip()))
    cards.sort(key=lambda x: (x[0], x[1]))
    n = len(cards)
    if n:
        # Distance from the ring's center so neighbouring cards don't overlap
        # (card width 260px desktop, 180px phone; 8 cards gives the original 330px / 230px).
        r = round(260 / (2 * math.tan(math.pi / max(n, 3))) + 16)
        r_sm = round(180 / (2 * math.tan(math.pi / max(n, 3))) + 13)
        items = "\n".join(
            f'        <a class="strip-item" href="{slug}.html" style="--i:{i}"><img src="images/{img}" alt="{_attr(alt)}"><span>{_esc(label)}</span></a>'
            for i, (_, slug, img, alt, label) in enumerate(cards))
        body = (f'\n      <div class="carousel-3d-ring" style="--n:{n}; --r:{r}px; --r-sm:{r_sm}px">\n'
                f'{items}\n      </div>\n')
    else:
        body = "\n"
    start = text.index(CAROUSEL_START)
    start_line_end = text.index("-->", start) + 3
    end = text.index(CAROUSEL_END)
    new = text[:start_line_end] + body + text[end:]
    if new != text:
        page.write_text(new)
    print(f"  carousel: {n} cards")


def build_projects(header, footer):
    projects = load_folder("data/projects")
    proj_header = header_for(header, "Projects")

    for p in projects:
        hero_block = (
            f'<img class="project-photo-main" src="images/{p["hero_image"]}" alt="{p["hero_alt"]}">'
            if p.get("hero_image") else
            '<div class="project-photo-main-placeholder"><span>Photos coming soon</span></div>'
        )
        source_note = (
            f'<div class="source-note">&#9733; {p["source_note"]}</div>' if p.get("source_note") else ""
        )
        paragraphs = "\n    ".join(f"<p>{para}</p>" for para in p["paragraphs"])
        team_block = (
            f'<div class="project-team"><h3>Project Team &amp; Partners</h3><p>{p["team_credit"]}</p></div>'
            if p.get("team_credit") else ""
        )
        if p.get("gallery"):
            imgs = "\n      ".join(
                f'<img src="images/{g["image"]}" alt="{g["alt"]}">' for g in p["gallery"]
            )
            gallery_block = (
                '<h2 style="font-family:var(--display); text-transform:uppercase; '
                'font-size:20px; margin:36px 0 6px;">More From This Project</h2>\n'
                f'    <div class="project-gallery">\n      {imgs}\n    </div>'
            )
        else:
            gallery_block = ""

        meta_desc = seo_desc_for(p)
        html = PROJECT_DOC.format(
            name=p["name"], tag=p["tag"], location=p["location"],
            header=proj_header, footer=footer, hero_block=hero_block,
            source_note=source_note, paragraphs=paragraphs,
            updates_block=updates_block_for(p),
            team_block=team_block, gallery_block=gallery_block,
            slug=p["slug"], meta_desc=meta_desc,
            seo_title=seo_title_for(p["name"], p["location"]),
            related_block=related_block_for(p, projects),
            meta_image=f'images/{p["hero_image"]}' if p.get("hero_image") else "images/og-share.jpg",
        )
        (ROOT / f'{p["slug"]}.html').write_text(html)

    # Regenerate the full gallery grid
    cards = []
    for p in projects:
        if p.get("hero_image"):
            photo = f'<div class="proj-photo"><img src="images/{p["hero_image"]}" alt="{p["hero_alt"]}"></div>'
        else:
            photo = '<div class="proj-photo placeholder"><span>Photo coming soon</span></div>'
        summary = p.get("summary") or (p["paragraphs"][0][:140] + "…" if p["paragraphs"] else "")
        addr_html = f'<p class="addr">{p["address"]}</p>' if p.get("address") else ""
        cards.append(f'''      <div class="proj-card">
        {photo}
        <div class="proj-body"><div class="tag">{p["tag"]}</div><h3>{p["name"]}</h3><p>{summary}</p>{addr_html}<a class="view-link" href="{p["slug"]}.html">View Project &raquo;</a></div>
      </div>''')

    grid_html = "\n".join(cards)
    total = len(projects)

    areas_map_html = extract_areas_map(
        "areas-leaflet-map", "560px",
        "From municipal parks to national retail builds, our work spans the Poconos, Greater Scranton, and the Lehigh Valley, all coordinated out of our Tobyhanna headquarters. Explore the map to see what we've built near you.")
    projects_page = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-9406J8G3G0"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-9406J8G3G0');
</script>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Concrete, Paving &amp; Construction Projects | Kobalt Construction</title>
<meta name="description" content="A look at the many commercial, residential, and public construction projects Kobalt Construction has completed across the Poconos and Northeastern PA.">
<link rel="canonical" href="https://kobaltconstruction.com/projects.html">
<link rel="icon" type="image/png" sizes="32x32" href="/images/favicon-32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/images/favicon-16.png">
<link rel="apple-touch-icon" sizes="180x180" href="/images/favicon-180.png">
<meta property="og:type" content="website">
<meta property="og:title" content="Concrete, Paving &amp; Construction Projects | Kobalt Construction">
<meta property="og:description" content="A look at the many commercial, residential, and public construction projects Kobalt Construction has completed across the Poconos and Northeastern PA.">
<meta property="og:url" content="https://kobaltconstruction.com/projects.html">
<meta property="og:image" content="https://kobaltconstruction.com/images/og-share.jpg">
<meta property="og:site_name" content="Kobalt Construction">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Concrete, Paving &amp; Construction Projects | Kobalt Construction">
<meta name="twitter:description" content="A look at the many commercial, residential, and public construction projects Kobalt Construction has completed across the Poconos and Northeastern PA.">
<meta name="twitter:image" content="https://kobaltconstruction.com/images/og-share.jpg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@400;500;600;700&family=Source+Sans+3:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="css/style.css">
</head>
<body>

{proj_header}

<section class="about-hero">
  <svg class="contours" viewBox="0 0 1180 300" preserveAspectRatio="none">
    <path d="M-50 260 Q 250 180 450 240 T 1230 250" fill="none" stroke="white" stroke-width="2"/>
    <path d="M-50 180 Q 270 100 470 160 T 1230 170" fill="none" stroke="white" stroke-width="2"/>
  </svg>
  <div class="wrap">
    <div class="eyebrow">Portfolio</div>
    <h1>Our Projects</h1>
    <p>A look at the many projects we have completed over the years across the Poconos and Northeast Pennsylvania.</p>
  </div>
</section>

{areas_map_html}
<section>
  <div class="wrap">
    <div class="proj-grid">
{grid_html}
    </div>
  </div>
</section>

<section class="cta-banner">
  <h2>Have a Project in Mind?</h2>
  <p>Tell us about it and we'll get back to you within one business day.</p>
  <a href="contact.html" class="btn btn-amber">Get a Quote</a>
</section>

{footer}

<script>
(function(){{
  // Scroll-reveal animation for sections (skips the first section to avoid hero flicker)
  var sections = document.querySelectorAll('section');
  if (sections.length > 1 && 'IntersectionObserver' in window) {{
    var revealObserver = new IntersectionObserver(function(entries){{
      entries.forEach(function(entry){{
        if (entry.isIntersecting) {{
          entry.target.classList.add('revealed');
          revealObserver.unobserve(entry.target);
        }}
      }});
    }}, {{ threshold: 0.12 }});
    sections.forEach(function(sec, i){{
      if (i === 0) return;
      sec.classList.add('reveal-section');
      revealObserver.observe(sec);
    }});
  }}

  // Photo gallery lightbox
  var galleryImgs = document.querySelectorAll('.project-gallery img');
  if (galleryImgs.length) {{
    var images = Array.prototype.map.call(galleryImgs, function(img){{ return {{ src: img.src, alt: img.alt }}; }});
    var current = 0;

    var lb = document.createElement('div');
    lb.className = 'kobalt-lightbox';
    lb.setAttribute('role', 'dialog');
    lb.setAttribute('aria-modal', 'true');
    lb.innerHTML =
      '<button class="kobalt-lightbox-close" aria-label="Close">&times;</button>' +
      '<button class="kobalt-lightbox-nav kobalt-lightbox-prev" aria-label="Previous photo">&#8249;</button>' +
      '<img alt="">' +
      '<button class="kobalt-lightbox-nav kobalt-lightbox-next" aria-label="Next photo">&#8250;</button>' +
      '<div class="kobalt-lightbox-count"></div>';
    document.body.appendChild(lb);

    var lbImg = lb.querySelector('img');
    var lbCount = lb.querySelector('.kobalt-lightbox-count');

    function show(i){{
      current = (i + images.length) % images.length;
      lbImg.src = images[current].src;
      lbImg.alt = images[current].alt;
      lbCount.textContent = (current + 1) + ' / ' + images.length;
    }}
    function openLightbox(i){{
      show(i);
      lb.classList.add('open');
      document.body.style.overflow = 'hidden';
    }}
    function closeLightbox(){{
      lb.classList.remove('open');
      document.body.style.overflow = '';
    }}

    galleryImgs.forEach(function(img, i){{
      img.addEventListener('click', function(){{ openLightbox(i); }});
    }});
    lb.querySelector('.kobalt-lightbox-close').addEventListener('click', closeLightbox);
    lb.querySelector('.kobalt-lightbox-prev').addEventListener('click', function(){{ show(current - 1); }});
    lb.querySelector('.kobalt-lightbox-next').addEventListener('click', function(){{ show(current + 1); }});
    lb.addEventListener('click', function(e){{ if (e.target === lb) closeLightbox(); }});
    document.addEventListener('keydown', function(e){{
      if (!lb.classList.contains('open')) return;
      if (e.key === 'Escape') closeLightbox();
      if (e.key === 'ArrowLeft') show(current - 1);
      if (e.key === 'ArrowRight') show(current + 1);
    }});
  }}
}})();
</script>

</body>
</html>
'''
    (ROOT / "projects.html").write_text(projects_page)
    print(f"  projects: regenerated {total} detail pages + projects.html")


def build_blog(header, footer):
    posts = load_folder("data/blog")
    blog_header = header_for(header, "Blog")

    for post in posts:
        paragraphs = "\n    ".join(f"<p>{para}</p>" for para in post["paragraphs"])
        meta_desc = post.get("summary") or (post["paragraphs"][0][:150] if post["paragraphs"] else post["title"])
        if post.get("original"):
            source_block = (
                '<div style="margin-top:36px; padding-top:20px; border-top:1px solid var(--line); font-size:13px; color:#5B6472;">'
                f'Written by the Kobalt Construction team{" &middot; " + post["published"] if post.get("published") else ""}. '
                'Have a question about your project? <a href="contact.html" style="color:var(--cobalt); font-weight:600; text-decoration:underline;">Get in touch</a>.</div>'
            )
        else:
            src_short = post.get("source_short", "NAHB.org")
            source_block = (
                '<div style="margin-top:36px; padding:20px 24px; background:var(--concrete); border-radius:6px;">'
                '<div style="font-size:12px; text-transform:uppercase; letter-spacing:.05em; color:var(--cobalt); font-weight:700; margin-bottom:6px;">Source</div>'
                f'<p style="font-size:14px; color:#444; margin-bottom:14px;">&ldquo;{post["source_title"]}&rdquo; &mdash; {post["source_publisher"]}, published {post["source_date"]}.</p>'
                f'<a class="btn btn-cobalt" href="{post["source_url"]}" target="_blank" rel="noopener">Read the Full Article at {src_short} &raquo;</a></div>'
                '<div style="margin-top:24px; padding-top:20px; border-top:1px solid var(--line); font-size:13px; color:#5B6472;">'
                f'Summarized by the Kobalt Construction team from {src_short} reporting (see source above). '
                'Have a question about your project? <a href="contact.html" style="color:var(--cobalt); font-weight:600; text-decoration:underline;">Get in touch</a>.</div>'
            )
        html = BLOG_DOC.format(
            title=post["title"], category=post["category"], header=blog_header, footer=footer,
            paragraphs=paragraphs, source_block=source_block,
            slug=post["slug"], meta_desc=meta_desc,
            seo_title=blog_seo_title(post["title"]),
            related_line=(
                f'<p style="margin-top:18px; font-size:14px;">Related service: '
                f'<a href="{post["related_href"]}" style="color:var(--cobalt); font-weight:600;">{post["related_label"]}</a></p>'
                if post.get("related_href") and post.get("related_label") else ""
            ),
        )
        (ROOT / f'{post["slug"]}.html').write_text(html)

    # Regenerate blog.html grid (preserve the association note by re-reading the current file)
    current_blog = (ROOT / "blog.html").read_text()
    note_match = re.search(r'(<section style="padding-bottom:0;">.*?</section>)', current_blog, re.DOTALL)
    note_block = note_match.group(1) if note_match else ""

    cards = []
    for post in posts:
        desc = post.get("summary") or (post["paragraphs"][0][:150] + "…" if post["paragraphs"] else "")
        cards.append(f'''      <div class="blog-card">
        <div class="eyebrow">{post["category"]}</div>
        <h3>{post["title"]}</h3>
        <p>{desc}</p>
        <a class="view-link" href="{post["slug"]}.html">Read Article &raquo;</a>
      </div>''')
    cards_html = "\n".join(cards)

    blog_page = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-9406J8G3G0"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-9406J8G3G0');
</script>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Blog | Kobalt Construction</title>
<meta name="description" content="Practical guidance from Kobalt Construction's crews on paving, stormwater, and site work, plus industry news on codes, safety, and costs.">
<link rel="canonical" href="https://kobaltconstruction.com/blog.html">
<link rel="icon" type="image/png" sizes="32x32" href="/images/favicon-32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/images/favicon-16.png">
<link rel="apple-touch-icon" sizes="180x180" href="/images/favicon-180.png">
<meta property="og:type" content="website">
<meta property="og:title" content="Blog | Kobalt Construction">
<meta property="og:description" content="Practical guidance from Kobalt Construction's crews on paving, stormwater, and site work, plus industry news on codes, safety, and costs.">
<meta property="og:url" content="https://kobaltconstruction.com/blog.html">
<meta property="og:image" content="https://kobaltconstruction.com/images/og-share.jpg">
<meta property="og:site_name" content="Kobalt Construction">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Blog | Kobalt Construction">
<meta name="twitter:description" content="Practical guidance from Kobalt Construction's crews on paving, stormwater, and site work, plus industry news on codes, safety, and costs.">
<meta name="twitter:image" content="https://kobaltconstruction.com/images/og-share.jpg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@400;500;600;700&family=Source+Sans+3:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="css/style.css">
</head>
<body>

{blog_header}

<section class="about-hero">
  <svg class="contours" viewBox="0 0 1180 300" preserveAspectRatio="none">
    <path d="M-50 260 Q 250 180 450 240 T 1230 250" fill="none" stroke="white" stroke-width="2"/>
    <path d="M-50 180 Q 270 100 470 160 T 1230 170" fill="none" stroke="white" stroke-width="2"/>
  </svg>
  <div class="wrap">
    <div class="eyebrow">From The Blog</div>
    <h1>Insights &amp; Updates</h1>
    <p>Whether you're a homeowner planning a renovation, a business owner looking for commercial construction advice, or just passionate about building, this is your go-to resource.</p>
  </div>
</section>

{note_block}

<section>
  <div class="wrap">
    <div class="blog-grid">
{cards_html}
    </div>
  </div>
</section>

<section class="cta-banner">
  <h2>Have a Project in Mind?</h2>
  <p>Tell us about it and we'll get back to you within one business day.</p>
  <a href="contact.html" class="btn btn-amber">Get a Quote</a>
</section>

{footer}

<script>
(function(){{
  // Scroll-reveal animation for sections (skips the first section to avoid hero flicker)
  var sections = document.querySelectorAll('section');
  if (sections.length > 1 && 'IntersectionObserver' in window) {{
    var revealObserver = new IntersectionObserver(function(entries){{
      entries.forEach(function(entry){{
        if (entry.isIntersecting) {{
          entry.target.classList.add('revealed');
          revealObserver.unobserve(entry.target);
        }}
      }});
    }}, {{ threshold: 0.12 }});
    sections.forEach(function(sec, i){{
      if (i === 0) return;
      sec.classList.add('reveal-section');
      revealObserver.observe(sec);
    }});
  }}

  // Photo gallery lightbox
  var galleryImgs = document.querySelectorAll('.project-gallery img');
  if (galleryImgs.length) {{
    var images = Array.prototype.map.call(galleryImgs, function(img){{ return {{ src: img.src, alt: img.alt }}; }});
    var current = 0;

    var lb = document.createElement('div');
    lb.className = 'kobalt-lightbox';
    lb.setAttribute('role', 'dialog');
    lb.setAttribute('aria-modal', 'true');
    lb.innerHTML =
      '<button class="kobalt-lightbox-close" aria-label="Close">&times;</button>' +
      '<button class="kobalt-lightbox-nav kobalt-lightbox-prev" aria-label="Previous photo">&#8249;</button>' +
      '<img alt="">' +
      '<button class="kobalt-lightbox-nav kobalt-lightbox-next" aria-label="Next photo">&#8250;</button>' +
      '<div class="kobalt-lightbox-count"></div>';
    document.body.appendChild(lb);

    var lbImg = lb.querySelector('img');
    var lbCount = lb.querySelector('.kobalt-lightbox-count');

    function show(i){{
      current = (i + images.length) % images.length;
      lbImg.src = images[current].src;
      lbImg.alt = images[current].alt;
      lbCount.textContent = (current + 1) + ' / ' + images.length;
    }}
    function openLightbox(i){{
      show(i);
      lb.classList.add('open');
      document.body.style.overflow = 'hidden';
    }}
    function closeLightbox(){{
      lb.classList.remove('open');
      document.body.style.overflow = '';
    }}

    galleryImgs.forEach(function(img, i){{
      img.addEventListener('click', function(){{ openLightbox(i); }});
    }});
    lb.querySelector('.kobalt-lightbox-close').addEventListener('click', closeLightbox);
    lb.querySelector('.kobalt-lightbox-prev').addEventListener('click', function(){{ show(current - 1); }});
    lb.querySelector('.kobalt-lightbox-next').addEventListener('click', function(){{ show(current + 1); }});
    lb.addEventListener('click', function(e){{ if (e.target === lb) closeLightbox(); }});
    document.addEventListener('keydown', function(e){{
      if (!lb.classList.contains('open')) return;
      if (e.key === 'Escape') closeLightbox();
      if (e.key === 'ArrowLeft') show(current - 1);
      if (e.key === 'ArrowRight') show(current + 1);
    }});
  }}
}})();
</script>

</body>
</html>
'''
    (ROOT / "blog.html").write_text(blog_page)
    print(f"  blog: regenerated {len(posts)} post pages + blog.html")


def build_service_pages(header, footer):
    """Concrete / Paving pages: copy lives in data/services/*.json, and the project
    cards are pulled automatically from every project tagged with that capability."""
    ga_block, end_script = read_shared_blocks()
    projects = load_folder("data/projects")
    svc_header = header_for(header, "Services")
    for path in sorted((ROOT / "data/services").glob("*.json")):
        s = json.loads(path.read_text())
        matches = [p for p in projects if s["capability"] in p.get("capabilities", [])]
        url = f"https://kobaltconstruction.com/{s['slug']}.html"
        title, desc = _esc(s["title"]), _attr(s["meta_description"])
        og_image = f"https://kobaltconstruction.com/images/{matches[0]['hero_image']}" if matches else "https://kobaltconstruction.com/images/og-share.jpg"
        intro = "\n    ".join(f'<p style="margin-bottom:14px;">{para}</p>' for para in s["intro"])
        cards = "\n".join(
            f'''      <div class="pillar-card">
        <svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="{c["icon"]}"/></svg>
        <div><h3>{c["title"]}</h3><p>{c["text"]}</p></div>
      </div>''' for c in s["cards"])
        evidence = "\n      ".join(f'<p><strong>{h["label"]}</strong> {h["html"]}</p>' for h in s["highlights"])
        see_also = " &middot; ".join(f'<a href="{x["href"]}">{x["label"]}</a>' for x in s["see_also"])
        proj_cards = "\n".join(
            f'''      <div class="proj-card">
        <div class="proj-photo"><img src="images/{p["hero_image"]}" alt="{_attr(p["hero_alt"])}"></div>
        <div class="proj-body"><div class="tag">{p["tag"]}</div><h3>{p["name"]}</h3><p>{p.get("summary", "")}</p><a class="view-link" href="{p["slug"]}.html">View Project &raquo;</a></div>
      </div>''' for p in matches)
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
{ga_block}
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<link rel="icon" type="image/png" sizes="32x32" href="/images/favicon-32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/images/favicon-16.png">
<link rel="apple-touch-icon" sizes="180x180" href="/images/favicon-180.png">
<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{og_image}">
<meta property="og:site_name" content="Kobalt Construction">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{og_image}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@400;500;600;700&family=Source+Sans+3:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="css/style.css">
</head>
<body>

{svc_header}

<section class="about-hero">
  <svg class="contours" viewBox="0 0 1180 300" preserveAspectRatio="none">
    <path d="M-50 260 Q 250 180 450 240 T 1230 250" fill="none" stroke="white" stroke-width="2"/>
    <path d="M-50 180 Q 270 100 470 160 T 1230 170" fill="none" stroke="white" stroke-width="2"/>
  </svg>
  <div class="wrap">
    <div class="eyebrow">{s["eyebrow"]}</div>
    <h1>{_esc(s["h1"])}</h1>
    <p style="color:#DCE4F0; max-width:640px; margin-top:14px;">{s["subtitle"]}</p>
  </div>
</section>

<section>
  <div class="wrap" style="max-width:900px;">
    {intro}
    <h2 style="font-family:var(--display); text-transform:uppercase; font-size:22px; margin:36px 0 20px;">{s["includes_heading"]}</h2>
    <div class="pillar-grid">
{cards}
    </div>
  </div>
</section>

<section class="services" style="padding-top:56px; padding-bottom:56px;">
  <div class="wrap" style="max-width:900px;">
    <h2 style="font-family:var(--display); text-transform:uppercase; font-size:22px; margin-bottom:20px;">{s["highlights_heading"]}</h2>
    <div class="evidence">
      {evidence}
    </div>
    <h2 style="font-family:var(--display); text-transform:uppercase; font-size:22px; margin:36px 0 12px;">{s["areas_heading"]}</h2>
    <p>{s["areas"]}</p>
    <p class="see-also">Related: {see_also}</p>
  </div>
</section>

<section style="padding-top:0;">
  <div class="wrap">
    <div class="section-head">
      <div class="eyebrow">Related Work</div>
      <h2>{s["projects_heading"]}</h2>
    </div>
    <div class="proj-grid">
{proj_cards}
    </div>
  </div>
</section>

<section class="cta-banner">
  <h2>{s["cta_heading"]}</h2>
  <p>{s["cta_text"]}</p>
  <a href="contact.html" class="btn btn-amber">Get a Quote</a>
</section>

{footer}

{end_script}
</body>
</html>
'''
        (ROOT / f"{s['slug']}.html").write_text(html)
        print(f"  service page: {s['slug']}.html ({len(matches)} projects)")


def build_sitemap():
    """Regenerate sitemap.xml from every page in the repo root so new CMS pages are always included."""
    base = "https://kobaltconstruction.com"
    high = {"projects.html", "services.html", "contact.html", "careers.html", "concrete.html", "paving.html", "site-work.html", "bid-with-us.html"}
    redirect_file = ROOT / "data/redirects.json"
    stubs = {f"{r['from']}.html" for r in json.loads(redirect_file.read_text())} if redirect_file.exists() else set()
    entries = []
    for page in sorted(ROOT.glob("*.html")):
        if page.name == "404.html" or page.name in stubs:
            continue
        loc = f"{base}/" if page.name == "index.html" else f"{base}/{page.name}"
        prio = "1.0" if page.name == "index.html" else ("0.8" if page.name in high else ("0.7" if page.stem in {p.stem for p in (ROOT / "data/areas").glob("*.json")} else "0.6"))
        entries.append(f"  <url>\n    <loc>{loc}</loc>\n    <priority>{prio}</priority>\n  </url>")
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(entries) + "\n</urlset>\n"
    (ROOT / "sitemap.xml").write_text(xml)
    print(f"  sitemap: {len(entries)} URLs")


def build_area_pages(header, footer):
    """Service-area pages: copy lives in data/areas/*.json; project cards and the capability
    summary are derived from the project data, so they stay accurate as projects are added."""
    ga_block, end_script = read_shared_blocks()
    projects = {p["slug"]: p for p in load_folder("data/projects")}
    areas = [json.loads(p.read_text()) for p in sorted((ROOT / "data/areas").glob("*.json"))]
    area_header = header_for(header, "Projects")
    caps = (("sitework", "site work", "site-work.html"), ("concrete", "concrete", "concrete.html"), ("paving", "paving", "paving.html"))
    for a in areas:
        matches = [projects[s] for s in a["projects"] if s in projects]
        url = f"https://kobaltconstruction.com/{a['slug']}.html"
        title, desc = _esc(a["title"]), _attr(a["meta_description"])
        og_image = "https://kobaltconstruction.com/images/og-share.jpg"
        intro = "\n    ".join(f'<p style="margin-bottom:14px;">{para}</p>' for para in a["intro"])
        parts = []
        for key, name, href in caps:
            n = sum(1 for p in matches if key in p.get("capabilities", []))
            if n:
                parts.append(f'<a href="{href}">{name}</a> on {n}')
        summary = ""
        if parts:
            joined = parts[0] if len(parts) == 1 else (" and ".join(parts) if len(parts) == 2 else ", ".join(parts[:-1]) + ", and " + parts[-1])
            summary = f'<p style="margin-bottom:14px;">Across these {len(matches)} projects, our crews handled {joined}.</p>'
        cards = "\n".join(
            f'''      <div class="proj-card">
        <div class="proj-photo"><img src="images/{p["hero_image"]}" alt="{_attr(p["hero_alt"])}"></div>
        <div class="proj-body"><div class="tag">{p["tag"]}</div><h3>{p["name"]}</h3><p>{p.get("summary", "")}</p><a class="view-link" href="{p["slug"]}.html">View Project &raquo;</a></div>
      </div>''' for p in matches)
        others = " &middot; ".join(f'<a href="{o["slug"]}.html">{o["short"]}</a>' for o in areas if o["slug"] != a["slug"])
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
{ga_block}
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<link rel="icon" type="image/png" sizes="32x32" href="/images/favicon-32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/images/favicon-16.png">
<link rel="apple-touch-icon" sizes="180x180" href="/images/favicon-180.png">
<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{og_image}">
<meta property="og:site_name" content="Kobalt Construction">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{og_image}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@400;500;600;700&family=Source+Sans+3:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="css/style.css">
</head>
<body>

{area_header}

<section class="about-hero">
  <svg class="contours" viewBox="0 0 1180 300" preserveAspectRatio="none">
    <path d="M-50 260 Q 250 180 450 240 T 1230 250" fill="none" stroke="white" stroke-width="2"/>
    <path d="M-50 180 Q 270 100 470 160 T 1230 170" fill="none" stroke="white" stroke-width="2"/>
  </svg>
  <div class="wrap">
    <div class="eyebrow">{a["eyebrow"]}</div>
    <h1>{_esc(a["h1"])}</h1>
    <p style="color:#DCE4F0; max-width:640px; margin-top:14px;">{a["subtitle"]}</p>
  </div>
</section>

<section>
  <div class="wrap" style="max-width:900px;">
    {intro}
    {summary}
  </div>
</section>

<section style="padding-top:0;">
  <div class="wrap">
    <div class="section-head">
      <div class="eyebrow">Projects</div>
      <h2>Our Work in {a["label"]}</h2>
    </div>
    <div class="proj-grid">
{cards}
    </div>
    <p class="see-also" style="text-align:center; margin-top:28px;">Also serving: {others}</p>
  </div>
</section>

<section class="cta-banner">
  <h2>{a["cta_heading"]}</h2>
  <p>{a["cta_text"]}</p>
  <a href="contact.html" class="btn btn-amber">Get a Quote</a>
</section>

{footer}

{end_script}
</body>
</html>
'''
        (ROOT / f"{a['slug']}.html").write_text(html)
        print(f"  area page: {a['slug']}.html ({len(matches)} projects)")


def build_redirects():
    """Old-site URLs (from the previous Duda site) that have no direct equivalent: write tiny
    pages that forward visitors and tell Google the new location. GitHub Pages cannot do
    server-side 301s, so this is the closest static-hosting equivalent."""
    rules = json.loads((ROOT / "data/redirects.json").read_text())
    for r in rules:
        target = r["to"]
        page = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>This page has moved | Kobalt Construction</title>
<meta http-equiv="refresh" content="0; url={target}">
<link rel="canonical" href="https://kobaltconstruction.com/{target}">
<script>window.location.replace("{target}");</script>
</head>
<body style="font-family:Arial,sans-serif; padding:40px; color:#21252B;">
<p>This page has moved. <a href="{target}" style="color:#1B3F73; font-weight:700;">Continue to the new page</a>.</p>
</body>
</html>
'''
        dest = ROOT / f"{r['from']}.html"
        if dest.exists() and "This page has moved" not in dest.read_text():
            print(f"  WARNING: redirect '{r['from']}' skipped because a real page already uses that address")
            continue
        dest.write_text(page)
    print(f"  redirects: {len(rules)} old URLs forwarded")


def main():
    header, footer = read_header_footer()
    print("Building site from data/*.json ...")
    build_projects(header, footer)
    build_home_updates()
    build_carousel()
    build_blog(header, footer)
    build_service_pages(header, footer)
    build_area_pages(header, footer)
    build_redirects()
    build_sitemap()
    from optimize_html import optimize_html
    optimize_html()
    print("Done.")


if __name__ == "__main__":
    main()
