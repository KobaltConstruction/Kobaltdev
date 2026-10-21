"""Site audit: run before every push (GitHub also runs the fast checks on every push).

    python3 scripts/audit.py              fast checks: content data, links, photos, SEO, forms
    python3 scripts/audit.py --rebuild    also confirm a fresh build reproduces the committed site
    python3 scripts/audit.py --browser    also run accessibility + phone-width checks in Chromium
                                          (needs: pip install playwright; npm install axe-core)

FAIL lines must be fixed (the script exits with an error). CHECK lines are
things a person should look at: they don't block a push.
Needs: pip install pillow beautifulsoup4
"""
import argparse, collections, glob, json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)

HAND_WRITTEN = {
    "index", "about", "services", "commercial", "residential", "public", "general-contracting",
    "design-and-consultation", "bid-with-us", "careers", "cdl-truck-driver", "laborer",
    "cement-finisher", "equipment-operator", "contact", "faq", "legal-policies", "404",
}
HUBS = {"projects", "blog"}
FORM_PAGES = ("contact", "bid-with-us", "cdl-truck-driver", "laborer", "cement-finisher", "equipment-operator")
TAGS = {"Commercial", "Public", "Residential"}
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
from datetime import date
TODAY = date.fromisoformat(os.environ["KOBALT_BUILD_DATE"]) if os.environ.get("KOBALT_BUILD_DATE") else date.today()
UPDATE_WINDOW_DAYS = 90         # keep in step with scripts/build.py
newest_update = [None]
carousel_count = [0]
THIN_WORDS = 90                 # project write-ups shorter than this read as thin
BIG_PHOTO_BYTES = 1_500_000     # originals larger than this slow the page down
BIG_PHOTO_WIDTH = 2400
# Wording that must be backed by real documentation before it goes live (see handoff Section 8).
CLAIM_WORDS = re.compile(
    r"\b(licen[sc]ed|bonded|insured|certified|certification|OSHA|award[- ]?winning|largest|"
    r"leading|best in|#1|guarantee[ds]?|warrant(y|ies)|years of experience|\d+\+? years)\b|\$\s?\d|\d+\s?%",
    re.I)

fails, checks = [], []
def FAIL(where, msg): fails.append(f"FAIL  {where}: {msg}")
def CHECK(where, msg): checks.append(f"CHECK {where}: {msg}")


def load(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as e:
        FAIL(path, f"not valid JSON ({e})")
        return None


def photo_name(v):
    v = (v or "").strip()
    for prefix in ("/images/", "images/"):
        if v.startswith(prefix):
            return v[len(prefix):]
    return v


def check_photo(where, name, alt):
    from PIL import Image
    name = photo_name(name)
    if not name:
        FAIL(where, "photo field is empty")
        return
    if not (alt or "").strip():
        FAIL(where, f"photo {name} has no description (needed for accessibility and search)")
    path = ROOT / "images" / name
    if not path.exists():
        FAIL(where, f"photo images/{name} is missing (upload it to the images folder)")
        return
    if not name.lower().endswith((".jpg", ".jpeg")):
        CHECK(where, f"{name} is not a JPG, so no small phone-size copies are made; JPG is preferred for photos")
    if " " in name or name != name.lower():
        CHECK(where, f"photo filename '{name}' has spaces or capitals; lowercase-with-hyphens is safer")
    try:
        with Image.open(path) as im:
            w = im.width
    except Exception:
        FAIL(where, f"images/{name} can't be opened as an image")
        return
    size = path.stat().st_size
    if size > BIG_PHOTO_BYTES or w > BIG_PHOTO_WIDTH:
        CHECK(where, f"{name} is large ({size/1e6:.1f} MB, {w}px wide); resize to about 1600px wide before adding")


# ---------------------------------------------------------------- content data
def audit_data():
    services = {}
    for f in sorted(glob.glob("data/services/*.json")):
        s = load(f)
        if s:
            services[s.get("capability")] = f
    areas = {}
    for f in sorted(glob.glob("data/areas/*.json")):
        a = load(f)
        if a:
            areas[f] = a
    redirects = load("data/redirects.json") or []
    redirect_from = {r.get("from") for r in redirects}
    try:
        map_hrefs = {s.get("href") for s in json.loads(Path("images/areas-served-latlon.json").read_text())}
    except Exception:
        map_hrefs = set()
    home = Path("index.html").read_text(encoding="utf-8") if Path("index.html").exists() else ""

    projects, slugs, orders = {}, collections.Counter(), collections.Counter()
    for f in sorted(glob.glob("data/projects/*.json")):
        p = load(f)
        if not p:
            continue
        where = f
        for key in ("slug", "name", "tag", "location", "hero_image", "hero_alt", "summary"):
            if not str(p.get(key, "")).strip():
                FAIL(where, f"'{key}' is missing or empty")
        slug = p.get("slug", "")
        if slug and slug != Path(f).stem:
            FAIL(where, f"slug '{slug}' doesn't match the file name '{Path(f).stem}.json'")
        if slug and not SLUG_RE.match(slug):
            FAIL(where, f"slug '{slug}' must be lowercase letters, numbers and hyphens only")
        if slug in HAND_WRITTEN or slug in HUBS or slug in redirect_from:
            FAIL(where, f"slug '{slug}' would overwrite an existing page or old-address redirect")
        slugs[slug] += 1
        orders[p.get("order")] += 1
        if p.get("tag") and p["tag"] not in TAGS:
            FAIL(where, f"tag '{p['tag']}' must be one of {sorted(TAGS)}")
        for c in p.get("capabilities") or []:
            if c not in services:
                FAIL(where, f"capability '{c}' isn't a service page (use {sorted(k for k in services if k)})")
        paras = p.get("paragraphs") or []
        if not paras:
            FAIL(where, "no write-up paragraphs")
        words = sum(len(re.sub(r"<[^>]+>", " ", x).split()) for x in paras)
        if paras and words < THIN_WORDS:
            CHECK(where, f"write-up is thin ({words} words); aim for {THIN_WORDS}+ with what was built, scope, and outcome")
        if p.get("hero_image"):
            check_photo(where, p["hero_image"], p.get("hero_alt"))
        for i, g in enumerate(p.get("gallery") or []):
            check_photo(f"{where} gallery #{i+1}", g.get("image"), g.get("alt"))
        if not p.get("gallery"):
            CHECK(where, "no gallery photos")
        md = p.get("meta_description")
        if md and not 70 <= len(md) <= 160:
            CHECK(where, f"meta_description is {len(md)} characters; aim for 70-155")
        update_text = []
        seen_dates = set()
        for i, u in enumerate(p.get("updates") or []):
            uw = f"{where} update #{i+1}"
            try:
                d = date.fromisoformat(str(u.get("date", "")).strip()[:10])
            except ValueError:
                FAIL(uw, f"date '{u.get('date')}' must look like 2026-10-19")
                continue
            if d in seen_dates:
                FAIL(uw, f"two updates share the date {d}; each update needs its own date")
            seen_dates.add(d)
            if d > TODAY:
                CHECK(uw, f"dated {d}, in the future; it won't show on the homepage until then")
            if not str(u.get("headline", "")).strip():
                FAIL(uw, "headline is empty (it's what the homepage shows)")
            elif len(u["headline"]) > 110:
                CHECK(uw, f"headline is {len(u['headline'])} characters; under about 100 reads best on the homepage")
            if not u.get("text"):
                FAIL(uw, "no text paragraphs")
            if not u.get("photos"):
                CHECK(uw, "no photos; the homepage entry and carousel card look best with one")
            for j, g in enumerate(u.get("photos") or []):
                check_photo(f"{uw} photo #{j+1}", g.get("image"), g.get("alt"))
            update_text += [u.get("headline", "")] + list(u.get("text") or [])
            newest_update[0] = max(newest_update[0], d) if newest_update[0] else d
        car = p.get("carousel")
        if car:
            if not isinstance(car, dict) or not str(car.get("label", "")).strip():
                CHECK(where, "has a carousel entry with no label, so it isn't shown in Fresh Off the Job Site")
            else:
                carousel_count[0] += 1
                if len(car["label"]) > 28:
                    CHECK(where, f"carousel label '{car['label']}' is long; under about 24 characters fits the card")
                if car.get("image"):
                    check_photo(f"{where} carousel", car["image"], car.get("alt") or p.get("hero_alt"))
        text = " ".join([p.get("summary", ""), p.get("team_credit", ""), p.get("source_note", "")] + paras + update_text)
        hits = sorted({m.group(0) for m in CLAIM_WORDS.finditer(text)})
        if hits:
            CHECK(where, f"wording to verify before publishing: {', '.join(hits)}")
        if slug:
            projects[slug] = p
            if not any(slug in a.get("projects", []) for a in areas.values()):
                CHECK(where, "not listed on any area page (add the slug to a data/areas/*.json 'projects' list)")
            if f"{slug}.html" not in map_hrefs and f'"href": "{slug}.html"' not in home:
                CHECK(where, "no pin on the Areas Served map (the map lives in index.html; ask for a pin to be added)")
            if not Path(f"{slug}.html").exists():
                FAIL(where, f"{slug}.html hasn't been generated yet; run python3 scripts/build.py")
    if newest_update[0]:
        age = (TODAY - newest_update[0]).days
        left = UPDATE_WINDOW_DAYS - age
        if left < 0:
            CHECK("homepage", f"no project update in the last {UPDATE_WINDOW_DAYS} days, so the Latest From the Field strip is hidden; add an update to bring it back")
        elif left <= 21:
            CHECK("homepage", f"the newest project update drops off the homepage in {left} days; add a new one to keep the strip showing")
    if carousel_count[0] and not 4 <= carousel_count[0] <= 12:
        CHECK("homepage", f"Fresh Off the Job Site has {carousel_count[0]} cards; 6 to 12 looks best in the ring")
    for s, n in slugs.items():
        if s and n > 1:
            FAIL("data/projects", f"slug '{s}' is used by {n} projects")
    dup_orders = sorted(o for o, n in orders.items() if n > 1 and o is not None)
    if dup_orders:
        CHECK("data/projects", f"display order numbers used more than once: {dup_orders} (ties sort by file name)")

    posts = set()
    for f in sorted(glob.glob("data/blog/*.json")):
        b = load(f)
        if not b:
            continue
        for key in ("slug", "title", "category", "summary"):
            if not str(b.get(key, "")).strip():
                FAIL(f, f"'{key}' is missing or empty")
        if not b.get("paragraphs"):
            FAIL(f, "no paragraphs")
        slug = b.get("slug", "")
        if slug and slug != Path(f).stem:
            FAIL(f, f"slug '{slug}' doesn't match the file name")
        if slug and (slug in HAND_WRITTEN or slug in HUBS or slug in redirect_from or slug in projects):
            FAIL(f, f"slug '{slug}' would overwrite an existing page")
        if not b.get("original"):
            missing = [k for k in ("source_title", "source_publisher", "source_date", "source_url") if not b.get(k)]
            if missing:
                FAIL(f, f"summarizes an outside article but is missing {', '.join(missing)} (or tick 'Written by Kobalt')")
        rh = b.get("related_href")
        if rh and not rh.startswith("http") and not Path(rh.split("#")[0]).exists():
            FAIL(f, f"related link '{rh}' points to a page that doesn't exist")
        if b.get("original"):
            hits = sorted({m.group(0) for m in CLAIM_WORDS.finditer(" ".join(b.get("paragraphs") or []))})
            if hits:
                CHECK(f, f"wording to verify before publishing: {', '.join(hits)}")
        posts.add(slug)

    for f, a in areas.items():
        for s in a.get("projects", []):
            if s not in projects:
                FAIL(f, f"lists project '{s}' but data/projects/{s}.json doesn't exist")

    for r in redirects:
        to = (r.get("to") or "").split("#")[0]
        if to and not to.startswith("http") and not Path(to).exists():
            FAIL("data/redirects.json", f"'{r.get('from')}' forwards to {to}, which doesn't exist")

    # Pages the build no longer produces (it never deletes files on its own).
    stubs = {f"{r.get('from')}.html" for r in redirects}
    expected = {f"{x}.html" for x in HAND_WRITTEN | HUBS | set(projects) | posts}
    expected |= {f"{Path(f).stem}.html" for f in glob.glob("data/services/*.json")}
    expected |= {f"{Path(f).stem}.html" for f in glob.glob("data/areas/*.json")}
    for page in sorted(glob.glob("*.html")):
        if page not in expected and page not in stubs:
            CHECK(page, "no data file or known page produces this; if it was removed on purpose, delete the .html too")
    return stubs


# ---------------------------------------------------------------- built pages
def audit_pages(stubs):
    from bs4 import BeautifulSoup
    allp = set(glob.glob("*.html"))
    pages = sorted(allp - stubs)
    titles, descs = collections.defaultdict(list), collections.defaultdict(list)
    sitemap = Path("sitemap.xml").read_text() if Path("sitemap.xml").exists() else ""
    for p in pages:
        s = BeautifulSoup(Path(p).read_text(encoding="utf-8"), "html.parser")
        for a in s.find_all("a", href=True):
            h = a["href"].split("#")[0].split("?")[0].lstrip("/")
            if not h or h.startswith(("http", "mailto:", "tel:", "javascript:")):
                continue
            if (h.endswith(".html") and h not in allp) or (not h.endswith(".html") and not Path(h).exists()):
                FAIL(p, f"broken link to {h}")
        for img in s.find_all("img", src=True):
            src = img["src"]
            if not src.startswith(("http", "data:")) and not Path(src.lstrip("/")).exists():
                FAIL(p, f"missing image {src}")
            if not img.has_attr("alt"):
                FAIL(p, f"image {src} has no alt attribute")
            for part in (img.get("srcset") or "").split(","):
                u = part.strip().split(" ")[0]
                if u and not u.startswith("http") and not Path(u.lstrip("/")).exists():
                    FAIL(p, f"missing small photo copy {u} (run the build)")
        t = s.title.get_text(strip=True) if s.title else ""
        if not t:
            FAIL(p, "no <title>")
        titles[t].append(p)
        m = s.find("meta", attrs={"name": "description"})
        if p != "404.html":
            if not m or not m.get("content", "").strip():
                FAIL(p, "no meta description")
            else:
                descs[m["content"]].append(p)
            if f"/{p}<" not in sitemap and not (p == "index.html" and "kobaltconstruction.com/<" in sitemap):
                CHECK(p, "not in sitemap.xml (run the build)")
        n = len(s.find_all("h1"))
        if n != 1:
            FAIL(p, f"has {n} <h1> headings (needs exactly 1)")
    for t, ps in titles.items():
        if len(ps) > 1:
            FAIL(", ".join(ps), f"share the same title '{t}'")
    for d, ps in descs.items():
        if len(ps) > 1:
            CHECK(", ".join(ps), "share the same meta description")
    for name in FORM_PAGES:
        f = f"{name}.html"
        if not Path(f).exists():
            continue
        s = BeautifulSoup(Path(f).read_text(encoding="utf-8"), "html.parser")
        for l in s.find_all("label", attrs={"for": True}):
            target = s.find(id=l["for"])
            if target is None:
                FAIL(f, f"label '{l.get_text(strip=True)[:30]}' points to a field that doesn't exist")
            elif l.find_next_sibling() is not target:
                FAIL(f, f"label '{l.get_text(strip=True)[:30]}' isn't next to its field (likely mislabeled)")
        for form in s.find_all("form"):
            if form.get("action", "").startswith("https://formspree.io") and not form.find(attrs={"name": "_gotcha"}):
                FAIL(f, "form is missing the hidden _gotcha spam field")
    return pages


# ---------------------------------------------------------------- clean rebuild
def audit_rebuild():
    tmp = Path(tempfile.mkdtemp(prefix="kobalt-rebuild-")) / "site"
    shutil.copytree(ROOT, tmp, ignore=shutil.ignore_patterns(".git", "__pycache__"))
    r = subprocess.run([sys.executable, "scripts/build.py"], cwd=tmp, capture_output=True, text=True)
    if r.returncode:
        FAIL("scripts/build.py", "build failed:\n" + r.stderr[-1500:])
        return
    changed = []
    for path in sorted(tmp.rglob("*")):
        if path.is_dir() or "__pycache__" in path.parts:
            continue
        rel = path.relative_to(tmp)
        orig = ROOT / rel
        if not orig.exists() or orig.read_bytes() != path.read_bytes():
            changed.append(str(rel))
    shutil.rmtree(tmp.parent, ignore_errors=True)
    if changed:
        FAIL("rebuild", f"a fresh build changes {len(changed)} file(s), so the committed site is out of date "
             f"(run python3 scripts/build.py): {', '.join(changed[:12])}{' ...' if len(changed) > 12 else ''}")


# ---------------------------------------------------------------- browser checks
def find_axe():
    for c in (os.environ.get("AXE_PATH"), "/tmp/axe/node_modules/axe-core/axe.min.js",
              str(ROOT.parent / "node_modules/axe-core/axe.min.js"),
              str(Path.home() / "node_modules/axe-core/axe.min.js")):
        if c and Path(c).exists():
            return c
    return None


def audit_browser(pages):
    import http.server, threading, functools
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        CHECK("--browser", "skipped: pip install playwright (then python3 -m playwright install chromium)")
        return
    axe_path = find_axe()
    if not axe_path:
        CHECK("--browser", "accessibility scan skipped: run 'npm install axe-core' in /tmp/axe or set AXE_PATH")
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(ROOT)))
    srv.handle_error = lambda *a: None   # the browser cancelling a request mid-download is normal
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    block = ("https://fonts.googleapis.com/**", "https://fonts.gstatic.com/**", "https://www.googletagmanager.com/**",
             "https://cdnjs.cloudflare.com/**", "https://unpkg.com/**", "https://api.maptiler.com/**")
    axe = Path(axe_path).read_text() if axe_path else None
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        # Reduced motion turns off the scroll-reveal fade, which otherwise makes text
        # look faint (and fail contrast) while it is still fading in.
        d = b.new_page(viewport={"width": 1100, "height": 900}, reduced_motion="reduce")
        m = b.new_page(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
        for ctx in (d, m):
            for u in block:
                ctx.route(u, lambda r: r.abort())
        for p in pages:
            if axe:
                d.goto(f"{base}/{p}")
                d.wait_for_timeout(150)
                d.evaluate("document.querySelectorAll('.reveal-section').forEach(s=>s.classList.add('revealed'))")
                d.evaluate(axe)
                r = d.evaluate("axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa']}})")
                for v in r["violations"]:
                    FAIL(p, f"accessibility: {v['id']} ({len(v['nodes'])} element(s))")
            m.goto(f"{base}/{p}")
            w = m.evaluate("document.documentElement.scrollWidth")
            if w > 390:
                FAIL(p, f"scrolls sideways on a phone ({w}px wide at a 390px screen)")
        hp = b.new_page(reduced_motion="reduce")
        for u in block:
            hp.route(u, lambda r: r.abort())
        for width in (320, 360, 390, 414, 600, 768, 900, 901, 950, 1000, 1100, 1180, 1280, 1440):
            hp.set_viewport_size({"width": width, "height": 800})
            hp.goto(f"{base}/index.html")
            if hp.evaluate("document.documentElement.scrollWidth") > width:
                FAIL("index.html", f"header/page scrolls sideways at {width}px")
        b.close()
    srv.shutdown()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rebuild", action="store_true", help="confirm a fresh build reproduces the committed files")
    ap.add_argument("--browser", action="store_true", help="accessibility and phone-width checks in Chromium")
    ap.add_argument("--quiet", action="store_true", help="hide CHECK lines")
    args = ap.parse_args()

    stubs = audit_data()
    pages = audit_pages(stubs)
    if args.rebuild:
        audit_rebuild()
    if args.browser:
        audit_browser(pages)

    if not args.quiet:
        for line in checks:
            print(line)
    for line in fails:
        print(line)
    n_proj = len(glob.glob("data/projects/*.json"))
    n_blog = len(glob.glob("data/blog/*.json"))
    print(f"\n{len(pages)} pages, {len(stubs)} redirects, {n_proj} projects, {n_blog} blog posts | "
          f"{len(fails)} FAIL, {len(checks)} CHECK"
          + (" | rebuild checked" if args.rebuild else "") + (" | browser checked" if args.browser else ""))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
