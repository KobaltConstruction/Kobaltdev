# Kobalt Construction Website — Status as of Sep 3, 2026

## BIG MILESTONE: dev.kobaltconstruction.com is live and confirmed working
Real-world tested on the actual deployed site (not just previews) — hero
image displays correctly, navigation works, forms submit successfully.
User is letting it run for a few days to watch for anything breaking
before doing the real production launch.

## What's next — the actual go-live (do this after the waiting period)
This is genuinely the last stretch. In order:

1. **Switch from dev testing to production domain:**
   - Edit the `CNAME` file in the repo: change its content from
     `dev.kobaltconstruction.com` back to `kobaltconstruction.com`
   - In GitHub repo Settings → Pages, update the Custom domain field to
     `kobaltconstruction.com` to match
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
  (KobaltConstruction org, "Kobalt" repo).
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
