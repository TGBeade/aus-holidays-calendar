"""Western Australia school holidays — parsed from official term-date tables.

Source: https://www.education.wa.edu.au/future-term-dates

WA's markup differs from the generic (VIC) term-table shape, so it gets its own
parser here rather than using base.parse_term_tables:

  * Each year is introduced by an ``<h4>`` heading like "2026 Term dates"; the
    year lives there, not in a table caption.
  * Each year has two tables (Semester 1, Semester 2) whose rows are only two
    cells wide, with the whole span in one cell:
        ["Term 1", "Monday 2 February to Thursday 2 April"]
    (there are also explicit "Break" rows, which we ignore — deriving the breaks
    from consecutive terms also yields the summer break across the year boundary).

We collect every Term row across the page and hand the (start, end) ranges to
base.breaks_from_terms, exactly like the other table states. Verified 2026 dates
are seeded in data/seed/wa.csv as the safety net.
"""

import re

from ..models import HolidayEvent
from . import base

SOURCE_URL = "https://www.education.wa.edu.au/future-term-dates"

_TERM_RE = re.compile(r"(?i)^\s*term\s*\d")
# Term rows use " to " between the two dates; tolerate dash variants too.
_SPLIT_RE = re.compile(r"\s+(?:to|–|—|-)\s+")


def _year_for(table) -> int | None:
    """WA puts the year in the nearest preceding heading ('2026 Term dates')."""
    node = table
    while True:
        node = node.find_previous(re.compile(r"^h[1-6]$"))
        if node is None:
            return None
        m = re.search(r"(20\d\d)", node.get_text())
        if m:
            return int(m.group(1))


def _term_ranges(html: bytes) -> list[tuple]:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "lxml")
    terms: list[tuple] = []
    for table in soup.find_all("table"):
        year = _year_for(table)
        if not year:
            continue
        for tr in table.find_all("tr"):
            cells = [c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])]
            if len(cells) >= 2 and _TERM_RE.match(cells[0]):
                span = cells[1].replace("\xa0", " ")
                halves = _SPLIT_RE.split(span, maxsplit=1)
                start = base._loose_date(halves[0], year)
                end = base._loose_date(halves[-1], year)
                if start and end and end >= start:
                    terms.append((start, end))
    return terms


def fetch(years: range) -> list[HolidayEvent]:
    return base.breaks_from_terms(_term_ranges(base.http_get(SOURCE_URL)), "WA")
