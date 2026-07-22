"""New South Wales school holidays.

NSW publishes a separate iCal file per year, linked from
    https://education.nsw.gov.au/schooling/calendars/<year>
For each year in range we load that page, find the .ics link, and parse it.
The NSW feed also contains non-holiday calendar events, including teaching-week
markers and Education Week. Those are removed before the remaining events are
passed to the shared parser.
"""

import re
from urllib.parse import urljoin

from icalendar import Calendar

from ..models import HolidayEvent
from . import base


CALENDAR_PAGE = "https://education.nsw.gov.au/schooling/calendars/{year}"
EXCLUDED_EVENT_RE = re.compile(
    r"^(?:\[NSW\]\s*)?(?:Term\s+\d+\s+Week\s+\d+\b|Education\s+Week\b)",
    re.IGNORECASE,
)


def _find_ics_url(page_html: bytes, base_url: str) -> str | None:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(page_html, "lxml")
    for a in soup.find_all("a", href=True):
        if a["href"].lower().endswith(".ics"):
            return urljoin(base_url, a["href"])
    return None


def _remove_non_holiday_events(ics_data: bytes) -> bytes:
    """Remove NSW term-week and Education Week VEVENTs."""
    calendar = Calendar.from_ical(ics_data)
    calendar.subcomponents = [
        component
        for component in calendar.subcomponents
        if not (
            component.name == "VEVENT"
            and EXCLUDED_EVENT_RE.match(
                str(component.get("SUMMARY", "")).strip()
            )
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
        ics_data = _remove_non_holiday_events(base.http_get(ics_url))
        events.extend(
            base.events_from_ics(ics_data, "NSW", range(year, year + 1))
        )
    return events
