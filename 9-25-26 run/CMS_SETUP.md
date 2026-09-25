# GitHub Pages + Decap CMS Setup

## Part 1 — Get the site live on GitHub Pages

1. Create a free GitHub account if you don't have one, and a new **public**
   repository (Settings can stay default) — name it something like
   `kobalt-site`.
2. Upload every file from this project into that repo (drag-and-drop via
   GitHub's web "Add file > Upload files" works for this, or use GitHub
   Desktop if you'd rather not use the command line).
3. In the repo, go to **Settings > Pages**. Under "Build and deployment",
   set Source to **GitHub Actions**. That's it — the workflow already in
   `.github/workflows/build-deploy.yml` will build and publish the site
   automatically on every push.
4. Your site will be live at `https://YOUR-USERNAME.github.io/kobalt-site/`
   within a minute or two. Check the repo's "Actions" tab to watch it build.

## Part 2 — Turn on Decap CMS editing

Decap CMS needs a way to verify who's allowed to save changes to your repo.
With GitHub Pages hosting, the simplest path uses a **free Netlify account**
purely as an authorization relay — you are NOT hosting your site there,
just borrowing their free login-verification service.

1. **Edit `admin/config.yml`** in your repo: replace
   `YOUR-GITHUB-USERNAME/kobalt-site` with your actual GitHub
   username and repo name.
2. **Create a GitHub OAuth App:** GitHub.com → your profile photo → Settings
   → Developer settings → OAuth Apps → New OAuth App.
   - Application name: anything, e.g. "Kobalt Site CMS"
   - Homepage URL: your GitHub Pages URL
   - Authorization callback URL: `https://api.netlify.com/auth/done`
   - Save it, then generate a **Client Secret** — keep both the Client ID
     and Client Secret handy for the next step.
3. **Create a free Netlify account** (netlify.com — no credit card, no site
   needed). Create one blank "site" there (it can stay empty/unused).
4. In that Netlify site's **Site settings > Access & security > OAuth**,
   add your GitHub Client ID and Client Secret from step 2.
5. Visit `https://YOUR-USERNAME.github.io/kobalt-site/admin/` — you should
   see a "Login with GitHub" button. Log in with a GitHub account that has
   write access to the repo, and you're editing.

If a step's exact menu wording has shifted since this was written, Decap
CMS's own docs (decapcms.org/docs/github-backend) and GitHub's own OAuth
App docs are the source of truth — this workflow is a well-established,
widely-used pattern, but UI text can move around over time.

## What the CMS can edit

- **Projects** — add, edit, or remove any project. Upload photos directly
  in the form; the build step regenerates that project's page and the
  gallery automatically.
- **Blog Posts** — same idea, for the 5 blog articles.

Everything else (homepage, services pages, careers pages, About) is
hand-authored HTML and isn't touched by the CMS or the build script —
those still need direct edits (ask Claude, same as always).
