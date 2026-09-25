# Kobalt Construction Website — Status as of Sep 3, 2026

## BIG MILESTONE: dev.kobaltconstruction.com is live and confirmed working
Real-world tested on the actual deployed site (not just previews) — hero
image displays correctly, navigation works, forms submit successfully.
User is letting it run for a few days to watch for anything breaking
before doing the real production launch.

## What's next — the actual go-live (do this after the waiting period)
This is genuinely the last stretch. **Decision made: repurpose the
Kobaltdev repo directly as production** (not copy everything into the
separate "Kobalt" repo, which exists but will just stay empty/unused —
can be deleted later if desired). In order:

1. **Switch Kobaltdev from dev testing to production domain:**
   - Edit the `CNAME` file in the Kobaltdev repo: change its content from
     `dev.kobaltconstruction.com` back to `kobaltconstruction.com`
   - In the Kobaltdev repo's Settings → Pages, update the Custom domain
     field to `kobaltconstruction.com` to match
2. **Change the ROOT domain's A records at GoDaddy** (this is the one
   still not done — the dev subdomain was purely a safe way to test
   first): same 4 A records as before, Host `@`:
   `185.199.108.153`, `185.199.109.153`, `185.199.110.153`,
   `185.199.111.153`. The `www` CNAME was already fixed earlier and
   shouldn't need touching again.
   - Note: editing/deleting A records has repeatedly triggered GoDaddy's
     SMS 2FA, sent to an outside IT contact's phone who's been hard to
     reach live — asking him to just forward the text code (not a call)
     has been the workaround.
3. Wait for DNS propagation, then check "Enforce HTTPS" in GitHub Pages
   settings once it's available.
4. Verify the live kobaltconstruction.com site directly.
5. **Then**, only after confirming stability: begin decommissioning
   Quantifi Media (see below).

## Known unfinished technical item: custom build workflow is broken
The custom `.github/workflows/build-deploy.yml` (meant to auto-run the
Python build script and regenerate pages when Decap CMS makes an edit)
failed with a YAML error ("No event triggers defined in `on`") — almost
certainly introduced when the file was pasted into GitHub's web editor
and indentation shifted. **The site currently works fine anyway**,
because GitHub's own default "pages build and deployment" workflow is
serving it — but that default workflow does NOT run the Python build
step. This means: **Decap CMS editing won't actually regenerate pages
correctly until this workflow is fixed.** Needs the raw current file
content pulled from the repo and debugged properly (indentation-safe),
rather than re-pasted blind again.

## Decap CMS — scaffolding built, login setup still not done
`admin/config.yml` and `admin/index.html` exist and are configured
correctly for folder-based collections (`data/projects/*.json`,
`data/blog/*.json`). Still needed before anyone can actually log in and
use it:
- `admin/config.yml`'s repo field still has the placeholder
  `YOUR-GITHUB-USERNAME/kobalt-site` — needs to become the real repo
  (KobaltConstruction org, "Kobaltdev" repo).
- The GitHub OAuth App + free-Netlify-as-relay setup (CMS_SETUP.md Part 2)
  hasn't been done yet.
- The broken build workflow above should be fixed first, since CMS edits
  depend on it.

## Two real bugs found and fixed during dev testing (both live now)
- **Hero background image was invisible** — `css/style.css` referenced
  the image with a path relative to the CSS file's own location
  (`images/hero-bg.jpg`), which only worked in every prior preview
  because those always inlined the CSS. As a real separate file it
  resolved to a nonexistent path. Fixed to `/images/hero-bg.jpg`
  (root-relative). This was a latent bug the whole project — worth
  double-checking there isn't a similar issue anywhere else if new CSS
  background-images get added later.
- **Resume upload removed from all 4 job pages** — Kobalt's Formspree
  plan doesn't support file attachments on the free tier. Removed the
  file input and the now-unneeded `enctype="multipart/form-data"` from
  each job page's form tag. The "prefer a printable form? Download the
  PDF instead" fallback link is now the primary way applicants can send
  an actual resume file.

## Confirmed fully working
- Both forms (Contact → info@kobaltconstruction.com, Job Applications →
  hr@kobaltconstruction.com) — tested repeatedly, real emails received.
  Earlier spam-folder issue was traced to Claude's own repetitive test
  phrasing tripping Formspree's spam filter, not a real delivery problem.
- "Our Partners and Qualifications" section on About page (8 badges,
  2 have known link caveats — see below).
- Legal & Policies page (Privacy Policy, EEO statement, Accessibility
  statement) — linked from homepage footer only, not attorney-reviewed.
- All 25 projects, 5 blog posts (NAHB-sourced), all service pages.

## Known caveats still standing (not urgent, just worth remembering)
- Construction Journal's badge links to a domain that now redirects to
  ConstructConnect (they were acquired) — still functional, just not
  where the name implies.
- Mount Pocono Association's own domain is down (502 error) — badge
  links to a PoconoMountains.com directory listing instead.
- Legal & Policies content is solid boilerplate, not a substitute for
  actual attorney review, given the site collects personal data/resumes.

## Quantifi Media decommission — do this LAST, after the real launch is stable
1. Confirm nothing else is hosted by Quantifi (email is confirmed
   separate — Kobalt runs on Microsoft 365, unrelated to them).
2. Check the actual contract for required notice period (never been
   read/shared with Claude).
3. Send written cancellation referencing those terms.
4. Confirm old site is taken down/redirected and account fully closed.

## Naming note
"JustQ Solutions" and "Quantifi Media" are the same company — use
Quantifi Media (confirmed by the user).

---

# Update — Sep 4, 2026: Mobile nav fix, favicon, SEO batch

## GitHub workflow confirmed working
The custom `.github/workflows/build-deploy.yml` was previously showing red,
but this was confirmed to be a stale old run from before the file was
fixed — the file itself is valid (verified byte-for-byte against the live
repo via raw.githubusercontent.com) and current pushes work correctly.
GitHub Desktop is now the established workflow for pushing updates (clone
Kobaltdev repo → copy extracted update files in, overwrite → GitHub
Desktop auto-detects changes → commit → push). Much smoother than the
web-upload batching used earlier — recommended for all future updates.

## Real bug found and fixed: mobile navigation was completely broken
`@media(max-width:900px){ .navlinks{display:none;} }` hid the nav links
on any phone-sized screen with **no replacement** — this had been present
since the very first version of the site, undetected because no testing
throughout the project actually rendered at real mobile widths. Fixed
with a proper hamburger menu (animates to X, dropdown with all links,
active-page highlight preserved) across all 47 pages. Verified with an
actual Chromium browser via Playwright (found in this environment) —
wkhtmltoimage, used for most visual checks this whole project, turned out
to be unreliable for anything beyond basic CSS (grids, 3D transforms, and
apparently buttons too) and produced false negatives during verification.
Playwright is a better verification tool going forward when precision
matters.

## Two other real bugs found + fixed during live dev testing
- **Hero image was invisible** — CSS referenced `images/hero-bg.jpg`,
  which resolves relative to the CSS file's own location (`css/`), not
  the site root — a latent bug invisible in every prior preview because
  those always inlined CSS. Fixed to `/images/hero-bg.jpg`.
- **Resume upload removed** from all 4 job pages — Kobalt's Formspree
  plan doesn't support file attachments. The "download the PDF instead"
  link is now the only way to submit an actual resume file.

## SEO/technical batch added (Sep 4)
- Favicon: a "K" monogram in brand colors (cobalt + amber accent),
  generated in multiple sizes, linked on all 48 pages.
- Custom on-brand 404 page.
- Meta description + Open Graph + Twitter Card tags added to **all 48
  pages** — unique per page for hand-authored pages; `build.py` was
  extended to auto-generate these for project/blog pages too, so future
  CMS-added content gets them automatically.
- `sitemap.xml` (47 URLs) and `robots.txt` added.
- `LocalBusiness`/`GeneralContractor` JSON-LD structured data added to
  the homepage (address, phone, hours, areas served: Poconos, Scranton,
  Wilkes-Barre, Wyoming Valley, Lehigh Valley).
- **Important context for whoever picks this up**: none of this batch
  directly boosts Google rankings by itself (meta/OG tags affect
  click-through and social previews, not ranking; structured data is
  secondary). User's actual goal is ranking for "concrete/paving in the
  Poconos/Scranton" — the real levers for that are, in order: Google
  Business Profile (biggest lever, not yet started, deliberately saved
  for actual launch day), reviews, backlinks, and on-page keyword content.

## Pending — awaiting the user's boss's sign-off before proceeding
Two SEO items proposed but **not yet done**, explicitly paused so the
user can loop in their boss first:
1. **Keyword content pass** — working "concrete," "paving," "Poconos,"
   "Scranton" naturally into actual sentence copy on service pages (not
   just tags) — this is the one that actually supports the stated
   ranking goal.
2. **Image optimization audit** — systematic check of all project photos
   for page-speed improvement; compression was applied ad hoc as photos
   came in throughout the project, never audited as a whole.

## Also discussed, deliberately deferred to actual launch day
- **Google Business Profile** setup — the single biggest lever for local
  map-pack visibility for searches like "paving contractor Scranton."
  Needs the user's own Google account + business verification (often a
  mailed postcard). Claude will walk through this at launch.
- **Google Search Console** — free diagnostic tool showing which search
  terms actually surface the site and any crawl errors. Same timing.
- **Google Analytics (GA4)** — confirmed free, no realistic traffic
  ceiling for a business this size. User wants this. Needs the user to
  create the account and share the Measurement ID; Claude will wire in
  the tracking code once provided.

## Files not yet pushed to GitHub
The favicon/404/SEO batch (sitemap.xml, robots.txt, index.html's
structured data, and meta tags across all 48 pages) has been packaged
but not yet pushed via GitHub Desktop as of this save point.
