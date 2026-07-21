# CLAUDE.md — project context for Claude Code

## What this is
A self-updating calendar of **public + school holidays for every Australian
state/territory**, built for planning meetings involving people across the
country (Therapeutic Guidelines). It generates subscribable `.ics` files hosted
on GitHub Pages; users subscribe once in Outlook. See `README.md` for full
detail — this file is the quick orientation.

## How it works (one paragraph)
`python -m src.build` gathers public holidays from the `holidays` library
(rule-based, all 8 jurisdictions, national dates deduped to `[National]`) and
school holidays from per-state sources, then writes `.ics` files into `docs/`.
A weekly GitHub Action reruns it and commits changes. Each school source resolves
`live fetch → data/cache (last-known-good) → data/seed/<state>.csv → empty`, so a
broken department page never empties the calendar. Per-run health is written to
`docs/status.json`.

## Data sources
- Public holidays: `src/public_holidays.py` (the `holidays` library).
- School — official `.ics` feeds: QLD, NSW (per-year), TAS. **(live)**
- School — HTML term-date tables via `base.parse_term_tables`: VIC. **(live)**
- School — WA: its own parser in `src/school/wa.py` (its markup differs from
  VIC's — see that file). **(live)**
- School — ACT, NT, SA: their **official** department pages are Cloudflare-blocked
  (403 to any server, incl. GitHub Actions — see soft spots). Instead they read
  from a family of public **per-year** calendar sites via
  `base.breaks_from_term_pages`: **(live)**
    - SA:  `saschoolholidays.com.au/sa-school-holidays-<year>/`
    - NT:  `schoolholidaysnt.com.au/nt-school-holidays-<year>/`
    - ACT: `schoolholidaysact.com.au/act-school-holidays-<year>/`
  Each page has a `Term N | start | end` table with full dates; the parser walks
  consecutive yearly pages (this year → +5) and derives the between-term breaks.
- Verified seed data checked in (fallback only): VIC 2026–2028; WA/SA/ACT/NT 2026.

## First tasks (in order)
1. **Push and deploy** (I have the user's git/gh credentials locally):
   - Create the repo if it doesn't exist (`gh repo create aus-holidays-calendar --public --source=. --remote=origin` or ask the user).
   - `git init && git add . && git commit -m "Initial commit" && git branch -M main && git push -u origin main`
   - Set Actions write permission: repo Settings → Actions → General → Workflow permissions → **Read and write** (via `gh api` or tell the user — this is a settings toggle).
   - Enable Pages from branch `main` / folder `/docs` (via `gh api` or tell the user).
   - Trigger the workflow: `gh workflow run "Build calendars"`.
2. **Validate the scrapers.** After the first Actions run, read `docs/status.json`.
   For each state under `school`, `source` should be `live`. Any state showing
   `seed` or `none` means its scraper returned nothing and needs fixing.

## Fixing a broken scraper
- ICS states (QLD/NSW/TAS): check the feed/page URL still resolves; the parser is
  `base.events_from_ics`.
- Table states (VIC/WA/SA/ACT/NT): `base.parse_term_tables` expects a
  `Term | Start | Finish` HTML table with the year in a nearby heading/caption.
  The parser is **verified against VIC's markup**. If another state structures its
  page differently (e.g. a PDF, or "Break" rows instead of term rows), adapt
  `parse_term_tables` or give that state its own `fetch()`. Verify by fetching the
  live page and confirming the derived breaks match the seed for 2026.

## Known soft spots (don't "fix" without checking)
- **ACT/NT/SA official pages are Cloudflare-blocked (403)** from any server-side
  fetch — they serve Cloudflare's "Just a moment..." challenge. Verified on GitHub
  Actions three ways: default UA, a real browser UA, and a **full headless
  Chromium (Playwright)** — all 403 (the block is on the runner's datacenter IP
  reputation, not the client). So we don't hit the official pages at all; we read
  the community per-year sites listed under Data sources instead. Don't re-try the
  official pages with headers or a headless browser — it won't work from CI.
- **ACT/NT/SA live data is third-party** (community calendar sites, not the
  department). Their near-term dates match the official term dates (cross-checked
  for 2026); far-future years are those sites' projections. If one changes layout
  or goes down, that state falls back to cache → seed and `status.json` flags it —
  fix by adjusting the parser or refreshing the seed.
- WA/ACT/NT **summer-break end dates** (return in early 2027) in the seeds are
  provisional; WA now confirms them from the live scrape. Everything else in the
  seeds is verified against official sources.
- `holidays` library covers AFL Grand Final Day and other proclaimed holidays for
  announced years; far-future entries are rule-based estimates. This is expected —
  don't add a second public-holiday source unless a real discrepancy appears.
- DTSTAMP is a fixed constant (`src/config.py`) on purpose, so identical data
  yields byte-identical output and CI commits stay clean. Don't switch it to now().

## Ground rules from the user (Brad)
- Prefers a single evolving reference over scattered files; keep README/CLAUDE.md
  as the source of truth and update them when behaviour changes.
- Wants confirmed vs. estimated data clearly separated. Label directional guesses.
- Direct, concise, copy-paste-ready. One clear recommendation over a menu.

## Local dev
```bash
pip install -r requirements.txt
python -m src.build   # writes docs/*.ics + docs/status.json
```
