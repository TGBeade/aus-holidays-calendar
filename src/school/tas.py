"""Tasmania school holidays.

TAS (Department for Education, Children and Young People) publishes its term
dates directly on the term-dates page, grouped under per-year headings
("2026 School term dates ...") with each term as a "Term N" sub-heading followed
by a "D Month - D Month" date range. We scrape those whole-term ranges and derive
the between-term holiday breaks.

This replaces reading the department's Google-calendar .ics feed, which split
term time into weekly "Term N - Week M" events and only covered the current
year. Scraping the page is both cleaner (whole-term ranges) and more complete:
because the page lists two years at once, the summer break (Term 4 -> next year's
Term 1) falls out of breaks_from_terms() automatically.
"""

import re
from datetime import date

from ..models import HolidayEvent
from . import base


PAGE_URL = "https://www.decyp.tas.gov.au/learning/term-dates/"

_MONTHS = {
    m: i
    for i, m in enumerate(
        "january february march april may june july august september october "
        "november december".split(),
        1,
    )
}
_YEAR_RE = re.compile(r"(20\d\d).*term dates", re.IGNORECASE)
# Matches a term heading but NOT "Term N Holiday" -- breaks are derived from the
# term ranges (which also yields the summer break), so holiday headings are skipped.
_TERM_RE = re.compile(r"^\s*Term\s*[1-4]\s*$", re.IGNORECASE)
_RANGE_RE = re.compile(
    r"(\d{1,2})\s+([A-Za-z]+)\s*[\u2013\u2014-]\s*(\d{1,2})\s+([A-Za-z]+)"
)


def _parse_terms(html: bytes) -> list[tuple[date, date]]:
    """Read whole-term (start, end) ranges from the DECYP term-dates page.

    A "20NN ... term dates" heading sets the working year; each following
    "Term N" heading is paired with the "D Month - D Month" range in the text
    beneath it. Both dates take the working year (terms never cross new year).
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "lxml")
    year: int | None = None
    terms: list[tuple[date, date]] = []
    for heading in soup.find_all(["h2", "h3", "h4"]):
        text = heading.get_text(" ", strip=True)
        year_match = _YEAR_RE.search(text)
        if year_match:
            year = int(year_match.group(1))
            continue
        if year is None or not _TERM_RE.match(text):
            continue
        # Collect the text following the heading, up to the next heading.
        parts: list[str] = []
        node = heading.find_next_sibling()
        while node is not None and node.name not in ("h2", "h3", "h4"):
            parts.append(node.get_text(" ", strip=True))
            node = node.find_next_sibling()
        m = _RANGE_RE.search(" ".join(parts))
        if not m:
            continue
        start_month = _MONTHS.get(m.group(2).lower())
        end_month = _MONTHS.get(m.group(4).lower())
        if not start_month or not end_month:
            continue
        try:
            start = date(year, start_month, int(m.group(1)))
            end = date(year, end_month, int(m.group(3)))
        except ValueError:
            continue
        if end >= start:
            terms.append((start, end))
    return terms


def fetch(years: range) -> list[HolidayEvent]:
    terms = _parse_terms(base.http_get(PAGE_URL))

    # The page publishes ~two years (about 8 terms). Refuse suspicious data so
    # resolve() falls back to the last-known-good cache rather than publishing
    # bad breaks if the page layout ever changes.
    if len(terms) < 4:
        raise ValueError(
            f"TAS term-dates page yielded only {len(terms)} term ranges; "
            f"expected at least 4"
        )

    breaks = base.breaks_from_terms(sorted(set(terms)), "TAS")
    return [b for b in breaks if b.start.year in years or b.end.year in years]
