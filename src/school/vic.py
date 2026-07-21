"""Victoria school holidays — parsed from official term-date tables.

Source: https://www.vic.gov.au/school-term-dates-and-holidays-victoria
VIC publishes term dates as HTML tables; base.parse_term_tables reads them
and derives the between-term holiday breaks. Verified 2026 dates are seeded in
data/seed/vic.csv as the safety net, and the live scrape extends/refreshes
this on GitHub Actions.
"""

from ..models import HolidayEvent
from . import base

SOURCE_URL = "https://www.vic.gov.au/school-term-dates-and-holidays-victoria"


def fetch(years: range) -> list[HolidayEvent]:
    return base.parse_term_tables(base.http_get(SOURCE_URL), "VIC", years)
