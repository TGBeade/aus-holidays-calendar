"""Queensland school holidays.

QLD publishes an official, rolling iCalendar feed of school holiday periods.
We fetch and reparse it, tagging events as [QLD]. If the URL has moved, update
SOURCE_URL below (the department occasionally relocates it); the last-known-good
cache keeps the calendar populated in the meantime.
"""

from ..models import HolidayEvent
from . import base

SOURCE_URL = "https://education.qld.gov.au/about/Documents/qld-school-holidays.ics"


def fetch(years: range) -> list[HolidayEvent]:
    data = base.http_get(SOURCE_URL)
    return base.events_from_ics(data, "QLD", years)
