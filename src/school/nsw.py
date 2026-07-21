"""New South Wales school holidays.

NSW publishes a separate iCal file per year, linked from
    https://education.nsw.gov.au/schooling/calendars/<year>
For each year in range we load that page, find the .ics link, and parse it.

The events NSW ships are typically term-date markers; we derive the between-term
holiday breaks from consecutive terms so the calendar shows the actual break
periods (which is what you want for meeting planning). If NSW's page structure
changes, only `_find_ics_url` needs adjusting; the cache/seed fallback covers
the gap.
"""

from urllib.parse import urljoin

from ..models import HolidayEvent
from . import base

CALENDAR_PAGE = "https://education.nsw.gov.au/schooling/calendars/{year}"


def _find_ics_url(page_html: bytes, base_url: str) -> str | None:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(page_html, "lxml")
    for a in soup.find_all("a", href=True):
        if a["href"].lower().endswith(".ics"):
            return urljoin(base_url, a["href"])
    return None


def fetch(years: range) -> list[HolidayEvent]:
    events: list[HolidayEvent] = []
    for year in years:
        page_url = CALENDAR_PAGE.format(year=year)
        try:
            html = base.http_get(page_url)
        except Exception:
            continue
        ics_url = _find_ics_url(html, page_url)
        if not ics_url:
            continue
        events.extend(base.events_from_ics(base.http_get(ics_url), "NSW", range(year, year + 1)))
    return events
