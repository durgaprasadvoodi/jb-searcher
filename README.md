# Off-Campus Job Drives — GitHub-hosted job tracker

Runs entirely on GitHub's free tier:
- **GitHub Actions** scrapes offcampusjobdrives.com once a day (no PC needed)
- Results are committed to `docs/data/jobs.json` in this repo
- **GitHub Pages** serves a small web page (`docs/index.html`) that reads that
  JSON and shows a searchable, filterable table — viewable from any browser,
  phone included

## Setup (one-time, ~5 minutes)

1. **Create a new GitHub repo** (public or private both work) and push these
   files to it, keeping the folder structure exactly as-is:
   ```
   your-repo/
   ├── .github/workflows/daily-scrape.yml
   ├── docs/
   │   ├── index.html
   │   └── data/jobs.json
   ├── scraper.py
   └── requirements.txt
   ```

   ```bash
   git init
   git add .
   git commit -m "Initial commit: job tracker"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   git push -u origin main
   ```

2. **Enable GitHub Pages:**
   - Go to your repo → Settings → Pages
   - Under "Build and deployment", set Source to "Deploy from a branch"
   - Branch: `main`, Folder: `/docs`
   - Save. GitHub will give you a URL like
     `https://YOUR_USERNAME.github.io/YOUR_REPO/` — that's your live tracker page.

3. **Enable Actions write permissions** (needed so the daily job can commit
   updated data back to the repo):
   - Repo → Settings → Actions → General → Workflow permissions
   - Select "Read and write permissions" → Save

4. **Run it once manually to seed data** (don't wait for the schedule):
   - Repo → Actions tab → "Daily Job Scrape" workflow → "Run workflow" button
   - Wait ~1-2 minutes, then refresh your GitHub Pages URL — you should see jobs.

That's it. From here on, it runs automatically every day at the time set in
`.github/workflows/daily-scrape.yml` (default 03:00 UTC / 8:30 AM IST — edit
the cron line to change this), and your Pages URL always reflects the latest
data.

## Files

- **`scraper.py`** — headless scraper (no GUI). Fetches the homepage and
  "Fresher Jobs" category, opens each job post, and checks for phrases like
  "0-2 years", "fresher", "entry-level" using regex. Merges new jobs into
  `docs/data/jobs.json` without duplicating or losing existing entries.
- **`.github/workflows/daily-scrape.yml`** — the GitHub Actions schedule.
  Also runnable manually anytime from the Actions tab.
- **`docs/index.html`** — the viewer page. Pure HTML/JS, no build step.
  Fetches `data/jobs.json` and renders a filterable table client-side.
- **`docs/data/jobs.json`** — the database, essentially. A dict keyed by job
  URL so re-runs don't create duplicates.

## Customizing the experience filter

Edit the `EXPERIENCE_PATTERNS` list near the top of `scraper.py` to adjust
what counts as a match — e.g. add patterns for specific phrasing you notice
the site using that isn't being caught yet. After editing, either wait for
the next scheduled run or trigger the workflow manually to re-check.

## Notes

- Only *new* job links get fetched and checked each run (existing links in
  `jobs.json` are skipped) — this keeps runs fast and avoids re-hammering the
  site with requests for jobs you already have.
- If a run finds zero new jobs, no commit is made (the workflow only commits
  when `docs/data/jobs.json` actually changed).
- Everything here is free: GitHub Actions gives 2,000 free minutes/month for
  private repos (unlimited for public repos), and GitHub Pages hosting is
  free for both.
