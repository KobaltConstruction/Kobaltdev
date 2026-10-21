# Kobalt Construction website

Source files for the Kobalt Construction website, hosted on GitHub Pages.

- Hand-written pages (edit directly): home, about, services, commercial, residential, public, general contracting, design and consultation, careers and job pages, FAQ, contact, legal, and bid-with-us.
- Generated pages (do not edit by hand): project pages, blog posts, the concrete, paving, and site-work pages, area pages, redirect pages, the projects and blog hubs, and sitemap.xml. They are rebuilt from the files in `data/` each time you run `python3 scripts/build.py` (GitHub also runs it on every push).
- The build needs Python 3 and Pillow (`pip install pillow`).
- Before pushing, run `python3 scripts/build.py` and then `python3 scripts/audit.py` (needs `pip install beautifulsoup4`). Lines marked FAIL must be fixed; GitHub runs the same audit on every push and won't publish while any FAIL remains. Lines marked CHECK are reminders (thin write-ups, wording to verify, project not on the map yet). Add `--rebuild` to confirm the committed pages are up to date, and `--browser` for accessibility and phone-width checks.
- Photos: put originals in `images/` (JPG, about 1600px wide). Phone-size copies in `images/sm/` are made automatically; `images/sm/manifest.json` records which originals they were made from, so only new or replaced photos get remade.
- Content editor setup notes: `CMS_SETUP.md`.
