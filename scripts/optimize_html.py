"""Post-build pass over every page: faster loading with no visual change.
- width/height on every local image (stops layout jumping while photos load)
- loading="lazy" + decoding="async" on photos below the first screen
- preconnect to Google's font host, hero preload on the homepage
- the shared js/site.js script
Safe to run repeatedly (each step is skipped if already applied)."""
import hashlib, json, re
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
EAGER = ("logo-img", "project-photo-main")      # always above the fold
NO_SRCSET = ("project-photo-main", "logo-img")   # displayed large: keep the full-size file
WIDTHS = (480, 800)
SIZES = "(max-width: 700px) 100vw, 400px"
_dims = {}


MANIFEST = ROOT / "images" / "sm" / "manifest.json"
_manifest = None
_manifest_dirty = False


def _fingerprint(path):
    return hashlib.sha1(path.read_bytes()).hexdigest()[:16]


def _load_manifest():
    global _manifest
    if _manifest is None:
        try:
            _manifest = json.loads(MANIFEST.read_text())
        except Exception:
            _manifest = {}
    return _manifest


def save_manifest():
    """Write images/sm/manifest.json if anything changed (called at the end of optimize_html)."""
    global _manifest_dirty
    if _manifest_dirty and _manifest is not None:
        MANIFEST.parent.mkdir(exist_ok=True)
        MANIFEST.write_text(json.dumps(dict(sorted(_manifest.items())), indent=1) + "\n")
        _manifest_dirty = False


def _variants(rel):
    """Create images/sm/<name>-480.jpg and -800.jpg and return their paths.

    Small copies are remade only when they are missing or the original photo's
    contents changed (tracked by fingerprint in images/sm/manifest.json).
    File dates are NOT used: git resets them on every checkout, which used to
    make GitHub remake random photos and commit them back on every push."""
    global _manifest_dirty
    if not rel.lower().endswith((".jpg", ".jpeg")) or not rel.startswith("images/") or "/sm/" in rel:
        return []
    src = ROOT / rel
    out = []
    try:
        manifest = _load_manifest()
        fp = _fingerprint(src)
        known = manifest.get(src.name)
        with Image.open(src) as im:
            for w in WIDTHS:
                if im.width <= w:
                    continue
                dest = ROOT / "images" / "sm" / f"{src.stem}-{w}.jpg"
                # Existing copy + no record yet: adopt it as-is (first run after this change).
                stale = not dest.exists() or (known is not None and known != fp)
                if stale:
                    dest.parent.mkdir(exist_ok=True)
                    h = round(im.height * w / im.width)
                    im.convert("RGB").resize((w, h), Image.LANCZOS).save(dest, "JPEG", quality=72, optimize=True)
                out.append((f"images/sm/{src.stem}-{w}.jpg", w))
            if known != fp:
                manifest[src.name] = fp
                _manifest_dirty = True
            out.append((rel, im.width))
    except Exception:
        return []
    return out if len(out) > 1 else []


def _size(rel):
    path = ROOT / rel.lstrip("/")
    if rel not in _dims:
        try:
            with Image.open(path) as im:
                _dims[rel] = im.size
        except Exception:
            _dims[rel] = None
    return _dims[rel]


def _fix_img(match):
    tag = match.group(0)
    src = re.search(r'\ssrc="([^"]+)"', tag)
    if not src or src.group(1).startswith(("http", "data:")):
        return tag
    extra = ""
    if " width=" not in tag and " height=" not in tag:
        size = _size(src.group(1))
        if size:
            extra += f' width="{size[0]}" height="{size[1]}"'
    cls = re.search(r'\sclass="([^"]*)"', tag)
    eager = bool(cls and any(c in cls.group(1).split() for c in EAGER))
    if " loading=" not in tag and not eager:
        extra += ' loading="lazy"'
    if " decoding=" not in tag:
        extra += ' decoding="async"'
    no_srcset = bool(cls and any(c in cls.group(1).split() for c in NO_SRCSET))
    if " srcset=" not in tag and not no_srcset:
        vs = _variants(src.group(1))
        if vs:
            extra += ' srcset="' + ", ".join(f"{p} {w}w" for p, w in vs) + f'" sizes="{SIZES}"'
    return tag[:-1] + extra + ">" if extra else tag


def optimize_html():
    rules = ROOT / "data/redirects.json"
    stubs = {f"{r['from']}.html" for r in json.loads(rules.read_text())} if rules.exists() else set()
    changed = 0
    for page in sorted(ROOT.glob("*.html")):
        if page.name in stubs:
            continue
        text = original = page.read_text()
        text = re.sub(r"<img\b[^>]*>", _fix_img, text)
        gs = '<link rel="preconnect" href="https://fonts.googleapis.com">'
        if gs in text and 'href="https://fonts.gstatic.com"' not in text:
            text = text.replace(gs, gs + '\n<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>', 1)
        if page.name == "index.html" and 'rel="preload"' not in text:
            text = text.replace("</head>", '<link rel="preload" as="image" href="/images/hero-bg.jpg" fetchpriority="high">\n</head>', 1)
        if 'src="js/site.js"' not in text and "</body>" in text:
            text = text.replace("</body>", '<script src="js/site.js" defer></script>\n</body>', 1)
        if text != original:
            page.write_text(text)
            changed += 1
    save_manifest()
    print(f"  optimize: {changed} pages updated")
