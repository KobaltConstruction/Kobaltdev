# Kobalt Construction Website — Status as of Sep 2, 2026 (evening)

## THE ONE THING BLOCKING LAUNCH RIGHT NOW
DNS at GoDaddy is the last step. Both **deleting** and **editing** the two old
A records (100.24.208.97 and 35.172.94.1) trigger GoDaddy's SMS 2FA prompt,
and that code goes to an outside IT contractor's phone who couldn't be
reached today. Nothing else is blocking — this is the only open item.

**Tomorrow, try in this order:**
1. See if the IT contact can just forward the SMS code via text (doesn't
   require an actual phone call — a much lower ask than trying to reach him
   live).
2. If reached, get the DNS changes done in one sitting (see exact records
   below) — should take 2 minutes once past the 2FA prompt.
3. Once saved, DNS can take a few minutes to 24-48 hours to propagate. Then:
   in the GitHub repo, Settings → Pages → check "Enforce HTTPS."

## Exact DNS records still needed at GoDaddy (kobaltconstruction.com)
Already done: `www` CNAME edited to point to `kobaltconstruction.github.io` ✅

Still needed — the two old A records need to become 4 correct ones:
- Delete or repoint away from: `100.24.208.97` and `35.172.94.1`
  (these point at Quantifi Media's old hosting)
- Should end up as 4 A records, Host `@`, values:
  `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`

**Do NOT touch:** both NS records, SOA, the `autodiscover` CNAME, the MX
record, or either TXT record — all of those are tied to Kobalt's Microsoft
365 email and Google verification, confirmed unrelated to the website.

## Everything else — DONE and confirmed working
- **Site is fully built**, hosted on GitHub Pages (repo: KobaltConstruction
  org, repo name "Kobalt"), Actions auto-deploy working, currently live at
  `kobaltconstruction.github.io/Kobalt/` — though that link itself will
  error until DNS above is finished, because a CNAME file already added to
  the repo makes GitHub auto-redirect that URL to the custom domain.
- **Both forms fully tested and confirmed working end-to-end**, multiple
  real test submissions received:
  - Contact form (Formspree ID `xjyvrkqz`) → delivers to
    info@kobaltconstruction.com
  - Job application form (Formspree ID `xrpggdpz`, used on all 4 job
    pages) → delivers to hr@kobaltconstruction.com
  - Earlier test emails were landing in spam — traced to Claude's own
    test-submission phrasing looking spammy (repeated "TEST SUBMISSION"
    boilerplate, placeholder email/phone) tripping Formspree's spam filter,
    not a real delivery problem. Confirmed fixed with natural-sounding test
    content — real applicants should be unaffected either way.
- **"Our Partners and Qualifications" section** added to the About page —
  8 clickable badges (styled icon+text, not literal copied logos) linking
  to real, verified org websites. Two flagged issues: Construction
  Journal's old domain now redirects to ConstructConnect (they were
  acquired); Mount Pocono Association's own domain (mtpoconoassn.com) is
  currently down (502 error), so that badge links to a directory listing
  on PoconoMountains.com instead — update if a better link surfaces.
- **Legal & Policies page** added (`legal-policies.html`) — Privacy Policy,
  Equal Opportunity Employer statement, Accessibility Statement. Linked
  only from the homepage footer (not site-wide) per instruction. This is
  solid starting-point boilerplate, not attorney-reviewed — worth a real
  legal look given the site collects personal data and resumes.
- **Decap CMS scaffolding built**: `data/projects/*.json` and
  `data/blog/*.json` (one file per project/post), `scripts/build.py`
  regenerates all project/blog pages + projects.html + blog.html from that
  data, `.github/workflows/build-deploy.yml` auto-builds and deploys on
  every push. Verified rigorously against the live site — output matches
  exactly (a few deliberate improvements included: fixed a pre-existing
  nav-highlighting bug on blog posts, restored some lost card
  summaries/alt-text along the way).
  - **Still not done**: the actual GitHub OAuth + free-Netlify-as-relay
    setup that lets someone log into `/admin/` and use the CMS UI. Steps
    are written out in `CMS_SETUP.md` Part 2. `admin/config.yml` still has
    a placeholder repo name (`YOUR-GITHUB-USERNAME/kobalt-site`) that
    needs to be swapped for the real one (KobaltConstruction org / Kobalt
    repo).
- **Workflow fix applied but needs pushing**: `build-deploy.yml`'s
  auto-commit step was changed to `continue-on-error: true`, so it won't
  break if branch protection blocks its direct push to main. **This
  updated file needs to be pushed to the GitHub repo** — not yet
  confirmed done.
- **Branch protection guidance given** for `main` (require PRs, don't
  block owner bypass) — not yet confirmed done on GitHub's side.

## Not started yet — later steps, in order
1. Confirm DNS fully resolved + HTTPS enforced (tomorrow's task).
2. Confirm the GitHub OAuth/Decap CMS login actually works end to end.
3. Let the new site run stable for at least a week before touching Quantifi.
4. Decommission Quantifi Media: confirm they don't host anything else
   (email is confirmed separate, on Microsoft 365 — good), check the
   actual contract for required notice period (never been read/shared),
   send written cancellation referencing those terms.
5. Whenever ready: staff → Claude → PR workflow for non-technical edits —
   foundation (branch protection) is being laid now but not activated.

## Naming note
"JustQ Solutions" and "Quantifi Media" are the same company — use
Quantifi Media (confirmed by the user).
