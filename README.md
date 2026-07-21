# Australian Holidays Calendar

One subscribable `.ics` calendar covering **public and school holidays for every
Australian state and territory** — built for planning meetings that involve people
across the country. Hosted entirely on GitHub, refreshed automatically, subscribe
once in Outlook and forget it.

## What you get

The build produces these calendars in `docs/` (served by GitHub Pages):

| File | Contents |
|------|----------|
| `all-states.ics` | **Primary.** Every public + school holiday, all states, each event prefixed `[VIC]`, `[NSW]`, `[National]`, … |
| `public-holidays.ics` | Public holidays only |
| `school-holidays.ics` | School holidays only |
| `by-state/<CODE>.ics` | One state's holidays + national public holidays |

School breaks are multi-day all-day events, so they show as banners across the
week in Outlook. Public holidays observed on the same day nationwide collapse to a
single `[National]` event; state-specific ones (King's Birthday, Labour Day, show
days) stay per-state.

## Setup (once)

1. **Fork / push** this repo to your GitHub account or org.
2. **Enable Pages:** repo **Settings → Pages → Build and deployment → Deploy from a
   branch → `main` / `docs`**. Your calendars are then at
   `https://<user>.github.io/<repo>/all-states.ics` (open `index.html` at the repo
   Pages root for a subscribe page with copy buttons).
3. **Run it once:** Actions tab → *Build calendars* → **Run workflow** (or just wait
   for the weekly run / any push to `src/`).
4. **Subscribe in Outlook:** Calendar → **Add calendar → Subscribe from web** →
   paste the `all-states.ics` URL.

## How it works

- **Public holidays** — the [`holidays`](https://pypi.org/project/holidays/) library
  computes all eight jurisdictions on the fly for any year, so there's no scraping
  and no "only published two years ahead" limit (this repo projects five years out).
- **School holidays** — mixed, because the states publish differently:
  - **QLD** — official rolling `.ics` feed, fetched and reparsed.
  - **NSW** — official per-year `.ics`, discovered from the calendar page.
  - **VIC, WA, SA, TAS, ACT, NT** — HTML pages (PDF in places); these need a
    per-state parser (see below) or a seed CSV.
- **Update loop** — `.github/workflows/build.yml` runs weekly (and on demand),
  regenerates the calendars, and commits any changes. GitHub Pages serves them at a
  stable URL, so subscribers never touch anything.

## School source detail

Every school source is implemented:

| State | Method | Notes |
|-------|--------|-------|
| QLD | official `.ics` feed | rolling feed, parsed directly — **live** |
| NSW | official per-year `.ics` | discovered from the calendar page — **live** |
| TAS | official `.ics` feed | link found on the term-dates page — **live** |
| VIC | `base.parse_term_tables` | reads the department's Term/Start/Finish tables and derives breaks — **live** |
| WA | `src/school/wa.py` | dedicated parser (year in `<h4>`, one-cell "start to finish" rows) — **live** |
| SA, NT, ACT | `base.breaks_from_term_pages` | official dept pages are **Cloudflare-blocked** from any server (403, confirmed on GitHub Actions incl. headless Chromium); instead these read public **per-year** community calendar sites (`saschoolholidays.com.au`, `schoolholidaysnt.com.au`, `schoolholidaysact.com.au`) and derive breaks from their term tables — **live**, years ahead. Seed CSV remains the fallback. |

The generic table parser pulls the year from each table's heading/caption, reads
the `Term | Start | Finish` rows (ignoring the "students start…" parenthetical),
and turns consecutive terms into the between-term breaks — the summer break is
produced automatically when Term 4 of one year is followed by Term 1 of the next.

**Validation note:** the table parser was verified against VIC's real page
structure (its output matches the seeded 2026 dates exactly). The QLD/NSW/TAS ICS
feeds and the other departments' table markup are fetched live on GitHub Actions;
if any department's markup differs from VIC's, only `base.parse_term_tables`
(or that state's `SOURCE_URL`) needs a tweak — the seed/cache keeps the calendar
correct meanwhile.

### Seed CSVs (verified safety net)

`data/seed/<state>.csv` (columns `summary,start,end`, ISO dates) holds
**verified official dates** so the calendar is correct even before a scraper's
first successful live run:

- VIC: 2026–2028 (from the approved 2026–2030 block)
- WA, SA, ACT, NT: 2026
- QLD, NSW, TAS: none — these populate live from their official `.ics` on the
  first Actions run (add a seed if you want pre-CI coverage)

WA/ACT/NT summer-break *end* dates (return in early 2027) are the one soft spot —
they confirm on the first live scrape. To add or correct any state, edit its seed
CSV; when the scraper succeeds, live data overwrites the cache automatically.

## Robustness

Each school source resolves through a fallback chain so one broken department page
never empties the calendar:

```
live fetch  →  last-known-good cache (data/cache/)  →  seed CSV (data/seed/)  →  empty
```

Every successful live fetch overwrites the cache. `docs/status.json` records where
each state's data came from on the last run, and the workflow raises a CI warning
listing any state running on seed-only or no data.

## Local development

```bash
pip install -r requirements.txt
python -m src.build          # writes docs/*.ics and docs/status.json
```

## Limitations (read these)

- **Proclamation-dependent public holidays** — one-off days (national mourning, some
  regional show days, VIC's AFL Grand Final Friday, which follows the fixture) may be
  missing or approximate, because they're declared each year rather than by rule.
- **Scraper fragility** — a department redesign breaks that state's parser; the cache
  keeps the calendar alive until you fix it, and `status.json` / the CI warning tell
  you which one.
- **Outlook refresh latency** — Outlook re-reads subscribed internet calendars on its
  own schedule (hours to ~a day). Fine here; these dates change about once a year.
- **Non-government schools** and border-region schools can differ by a day or two from
  the state government dates used here.
