"""New South Wales school holidays.

NSW publishes a separate iCal file per year, linked from
    https://education.nsw.gov.au/schooling/calendars/<year>
For each year in range we load that page, find the .ics link, and parse it.
The NSW feed also includes one event for every teaching week (for example,
"Term 3 Week 1 (10 Wk Term)"). Those events are removed before the remaining
calendar data is passed to the shared parser.

If NSW's page structure changes, only ``_find_ics_url`` needs adjusting; the
cache/seed fallback covers the gap.
"""

import re
from urllib.parse import urljoin

from icalendar import Calendar

from ..models import HolidayEvent
from . import base


CALENDAR_PAGE = "https://education.nsw.gov.au/schooling/calendars/{year}"
TERM_WEEK_RE = re.compile(
    r"^(?:\[NSW\]\s*)?Term\s+\d+\s+Week\s+\d+\b",
    re.IGNORECASE,
)


def _find_ics_url(page_html: bytes, base_url: str) -> str | None:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(page_html, "lxml")
    for a in soup.find_all("a", href=True):
        if a["href"].lower().endswith(".ics"):
            return urljoin(base_url, a["href"])
    return None


def _remove_term_week_events(ics_data: bytes) -> bytes:
    """Remove NSW teaching-week VEVENTs while retaining all other events."""
    calendar = Calendar.from_ical(ics_data)
    calendar.subcomponents = [
        component
        for component in calendar.subcomponents
        if not (
            component.name == "VEVENT"
            and TERM_WEEK_RE.match(str(component.get("SUMMARY", "")).strip())
        )
    ]
    return calendar.to_ical()


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
        ics_data = _remove_term_week_events(base.http_get(ics_url))
        events.extend(
            base.events_from_ics(ics_data, "NSW", range(year, year + 1))
        )
    return events
