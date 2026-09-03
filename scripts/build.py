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
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


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
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{name} | Kobalt Construction Projects</title>
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
    {paragraphs}
    {team_block}
    {gallery_block}
  </div>
</section>

<section class="cta-banner">
  <h2>Have a Project in Mind?</h2>
  <p>Tell us about it and we'll get back to you within one business day.</p>
  <a href="contact.html" class="btn btn-amber">Get a Quote</a>
</section>

{footer}

</body>
</html>
'''

BLOG_DOC = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} | Kobalt Construction Blog</title>
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
    <div style="margin-top:36px; padding:20px 24px; background:var(--concrete); border-radius:6px;">
      <div style="font-size:12px; text-transform:uppercase; letter-spacing:.05em; color:var(--cobalt); font-weight:700; margin-bottom:6px;">Source</div>
      <p style="font-size:14px; color:#444; margin-bottom:14px;">&ldquo;{source_title}&rdquo; &mdash; {source_publisher}, published {source_date}.</p>
      <a class="btn btn-cobalt" href="{source_url}" target="_blank" rel="noopener">Read the Full Article at {source_short} &raquo;</a>
    </div>
    <div style="margin-top:24px; padding-top:20px; border-top:1px solid var(--line); font-size:13px; color:#8A93A0;">
      Summarized by the Kobalt Construction team from {source_short} reporting (see source above). Have a question about your project? <a href="contact.html" style="color:var(--cobalt); font-weight:600;">Get in touch</a>.
    </div>
  </div>
</section>

<section class="cta-banner">
  <h2>Have a Project in Mind?</h2>
  <p>Tell us about it and we'll get back to you within one business day.</p>
  <a href="contact.html" class="btn btn-amber">Get a Quote</a>
</section>

{footer}

</body>
</html>
'''


def load_folder(folder):
    """Load every *.json file in a data folder, sorted by an explicit
    'order' field if present (Decap CMS folder collections don't guarantee
    file order, so we control display order via this field instead)."""
    items = []
    for path in sorted((ROOT / folder).glob("*.json")):
        items.append(json.loads(path.read_text()))
    items.sort(key=lambda x: x.get("order", 999))
    return items


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

        html = PROJECT_DOC.format(
            name=p["name"], tag=p["tag"], location=p["location"],
            header=proj_header, footer=footer, hero_block=hero_block,
            source_note=source_note, paragraphs=paragraphs,
            team_block=team_block, gallery_block=gallery_block,
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

    projects_page = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Projects | Kobalt Construction</title>
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
        html = BLOG_DOC.format(
            title=post["title"], category=post["category"], header=blog_header, footer=footer,
            paragraphs=paragraphs, source_title=post["source_title"],
            source_publisher=post["source_publisher"], source_date=post["source_date"],
            source_url=post["source_url"], source_short=post.get("source_short", "NAHB.org"),
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
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Blog | Kobalt Construction</title>
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

</body>
</html>
'''
    (ROOT / "blog.html").write_text(blog_page)
    print(f"  blog: regenerated {len(posts)} post pages + blog.html")


def main():
    header, footer = read_header_footer()
    print("Building site from data/*.json ...")
    build_projects(header, footer)
    build_blog(header, footer)
    print("Done.")


if __name__ == "__main__":
    main()
