"""Build a single-file offline preview of the site (all pages, images inlined, forms and analytics off).
Usage: python3 scripts/make_preview.py . kobalt-site-full-preview.html   (needs pillow). Do not commit the output."""
import base64, io, json, re, sys
from pathlib import Path
from PIL import Image

SITE = Path(sys.argv[1]); OUT = Path(sys.argv[2])
redirects = {r["from"] + ".html": r["to"] for r in json.loads((SITE / "data/redirects.json").read_text())}
pages = sorted(p.name for p in SITE.glob("*.html") if p.name not in redirects)

IMG_RE = re.compile(r'(?<![\w/.-])/?(images/[\w./-]+?\.(?:jpe?g|png|webp|gif|svg|ico))', re.I)
FILE_RE = re.compile(r'(?<![\w/.-])/?(files/[\w./-]+?\.pdf)', re.I)
assets, tokens = {}, {}

def token(rel):
    if rel not in tokens:
        tokens[rel] = f"__ASSET_{len(tokens)}__"
    return tokens[rel]

def encode(rel):
    path = SITE / rel
    if not path.exists():
        return None
    ext = path.suffix.lower()
    if ext in (".jpg", ".jpeg"):
        with Image.open(path) as im:
            im = im.convert("RGB")
            if im.width > 1100:
                im = im.resize((1100, round(im.height * 1100 / im.width)), Image.LANCZOS)
            buf = io.BytesIO(); im.save(buf, "JPEG", quality=74, optimize=True)
        return "image/jpeg", buf.getvalue()
    mime = {".png": "image/png", ".webp": "image/webp", ".gif": "image/gif", ".svg": "image/svg+xml",
            ".ico": "image/x-icon", ".pdf": "application/pdf"}[ext]
    return mime, path.read_bytes()

def clean(html):
    html = re.sub(r'<script async src="https://www\.googletagmanager\.com[^>]*></script>\s*', "", html)
    html = re.sub(r"<script>\s*window\.dataLayer.*?</script>\s*", "", html, flags=re.S)
    html = re.sub(r'\s(srcset|sizes)="[^"]*"', "", html)
    html = html.replace(' loading="lazy"', "")          # previews use the one inlined photo
    html = re.sub(r'<link rel="preload"[^>]*>\s*', "", html)
    html = html.replace('<link rel="stylesheet" href="css/style.css">', "<style>__SITE_CSS__</style>")
    html = re.sub(r'<script src="js/site\.js"[^>]*></script>', "<script>__SITE_JS__</script>", html)
    html = IMG_RE.sub(lambda m: token(m.group(1)), html)
    html = FILE_RE.sub(lambda m: token(m.group(1)), html)
    return html

page_html, titles = {}, {}
for name in pages:
    raw = (SITE / name).read_text(encoding="utf-8")
    t = re.search(r"<title>(.*?)</title>", raw, re.S)
    titles[name] = re.sub(r"\s+", " ", t.group(1)).strip() if t else name
    page_html[name] = clean(raw)
css = IMG_RE.sub(lambda m: token(m.group(1)), (SITE / "css/style.css").read_text())
js = (SITE / "js/site.js").read_text()

for rel, tok in tokens.items():
    enc = encode(rel)
    if enc:
        assets[tok] = [enc[0], base64.b64encode(enc[1]).decode()]

HAND = ["index", "about", "services", "commercial", "public", "residential", "general-contracting",
        "design-and-consultation", "concrete", "paving", "site-work", "projects", "bid-with-us", "careers",
        "contact", "faq", "blog", "legal-policies"]
groups = {"Main pages": [], "Areas": [], "Projects": [], "Jobs": [], "Blog": [], "Other": []}
for n in pages:
    s = n[:-5]
    if s in HAND: groups["Main pages"].append(n)
    elif s in ("pocono-mountains", "scranton", "wyoming-valley", "hazleton"): groups["Areas"].append(n)
    elif s.startswith("blog-"): groups["Blog"].append(n)
    elif s in ("cdl-truck-driver", "laborer", "cement-finisher", "equipment-operator"): groups["Jobs"].append(n)
    elif (SITE / f"data/projects/{s}.json").exists(): groups["Projects"].append(n)
    else: groups["Other"].append(n)
groups["Main pages"].sort(key=lambda n: HAND.index(n[:-5]))
options = "".join(
    f'<optgroup label="{g}">' + "".join(f'<option value="{n}">{titles[n].split(" | ")[0]}</option>' for n in ns) + "</optgroup>"
    for g, ns in groups.items() if ns)

data = json.dumps({"pages": page_html, "css": css, "js": js, "assets": assets, "redirects": redirects}).replace("</", "<\\/")
OUT.write_text(f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Kobalt Site Preview</title>
<style>
:root{{ --bar:#1B3F73; --barText:#fff; --amber:#E8A33D; --bg:#2a2e35; }}
*{{box-sizing:border-box}} html,body{{margin:0;height:100%;background:var(--bg);font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif}}
.bar{{display:flex;flex-wrap:wrap;gap:8px 12px;align-items:center;padding:8px 14px;background:var(--bar);color:var(--barText);font-size:14px}}
.bar strong{{letter-spacing:.04em}} .bar .note{{opacity:.8;font-size:12.5px}}
.bar select,.bar button{{font:inherit;border-radius:5px;border:1px solid rgba(255,255,255,.35);background:#fff;color:#1d2228;padding:5px 8px}}
.bar button{{background:transparent;color:#fff;cursor:pointer}} .bar button[aria-pressed="true"]{{background:var(--amber);border-color:var(--amber);color:#1d2228}}
.bar select{{max-width:min(420px,100%)}}
.stage{{height:calc(100% - 52px);display:flex;justify-content:center;overflow:auto}}
iframe{{border:0;background:#fff;width:100%;height:100%;transition:width .2s}}
.phone iframe{{width:390px;max-width:100%;box-shadow:0 0 0 1px #000}}
</style></head><body>
<div class="bar">
  <strong>Kobalt site preview</strong>
  <button id="back" type="button" title="Back">&larr; Back</button>
  <label>Page <select id="pick">{options}</select></label>
  <button id="desk" type="button" aria-pressed="true">Desktop</button><button id="phone" type="button" aria-pressed="false">Phone</button>
  <span class="note">Offline copy of all {len(pages)} pages. Forms are switched off here.</span>
</div>
<div class="stage" id="stage"><iframe id="view" title="Site preview"></iframe></div>
<script id="site-data" type="application/json">{data}</script>
<script>
(function(){{
  var D = JSON.parse(document.getElementById('site-data').textContent);
  var urls = {{}};
  Object.keys(D.assets).forEach(function(tok){{
    var a = D.assets[tok], bin = atob(a[1]), arr = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
    urls[tok] = URL.createObjectURL(new Blob([arr], {{type: a[0]}}));
  }});
  function fill(s){{ return s.replace(/__ASSET_\\d+__/g, function(t){{ return urls[t] || ''; }}); }}
  var css = fill(D.css), view = document.getElementById('view'), pick = document.getElementById('pick');
  var history = [], current = null;
  function load(name, hash, push){{
    if (D.redirects[name]) {{ var to = D.redirects[name].split('#'); name = to[0]; hash = hash || to[1]; }}
    if (!D.pages[name]) {{ name = 'index.html'; }}
    if (push !== false && current) history.push(current);
    current = name; pick.value = name;
    var html = fill(D.pages[name]).replace('__SITE_CSS__', function(){{ return css; }}).replace('__SITE_JS__', function(){{ return D.js; }});
    view.onload = function(){{
      var doc = view.contentDocument;
      doc.addEventListener('click', function(e){{
        var a = e.target.closest && e.target.closest('a[href]'); if (!a) return;
        var href = a.getAttribute('href');
        if (/^(https?:|mailto:|tel:)/.test(href)) {{ if (/^https?:/.test(href)) a.target = '_blank'; return; }}
        if (/^blob:/.test(href)) {{ a.target = '_blank'; return; }}
        if (href.charAt(0) === '#') return;
        var parts = href.replace(/^\\//, '').split('#');
        if (/\\.html$/.test(parts[0]) || parts[0] === '') {{ e.preventDefault(); load(parts[0] || 'index.html', parts[1]); }}
      }}, true);
      doc.addEventListener('submit', function(e){{
        e.preventDefault(); e.stopImmediatePropagation();
        var f = e.target, m = doc.createElement('p');
        m.textContent = 'Preview only: this form was not sent. On the live site it goes to Kobalt by email.';
        m.style.cssText = 'margin-top:14px;padding:12px 14px;border-radius:6px;background:#FFF4DE;color:#5a3d00;font-weight:600';
        f.appendChild(m);
      }}, true);
      if (hash) {{ var el = doc.getElementById(hash); if (el) el.scrollIntoView(); }} else view.contentWindow.scrollTo(0, 0);
    }};
    view.srcdoc = html;
  }}
  pick.addEventListener('change', function(){{ load(pick.value); }});
  document.getElementById('back').addEventListener('click', function(){{ if (history.length) load(history.pop(), null, false); }});
  var stage = document.getElementById('stage'), desk = document.getElementById('desk'), phone = document.getElementById('phone');
  desk.onclick = function(){{ stage.classList.remove('phone'); desk.setAttribute('aria-pressed','true'); phone.setAttribute('aria-pressed','false'); }};
  phone.onclick = function(){{ stage.classList.add('phone'); phone.setAttribute('aria-pressed','true'); desk.setAttribute('aria-pressed','false'); }};
  load('index.html', null, false);
}})();
</script>
</body></html>''', encoding="utf-8")
print(len(pages), "pages,", len(assets), "assets,", round(OUT.stat().st_size / 1e6, 1), "MB")
missing = [r for r, t in tokens.items() if t not in assets]
print("missing:", missing or "none")
