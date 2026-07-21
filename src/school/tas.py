"""Tasmania school holidays.

TAS (Department for Education, Children and Young People) publishes an official
.ics of term dates, linked from its term-dates page. We find that link and parse
the feed, deriving break periods from the term events.
"""

from ..models import HolidayEvent
from . import base

PAGE_URL = "https://www.decyp.tas.gov.au/learning/term-dates/"


def fetch(years: range) -> list[HolidayEvent]:
    ics_url = base.find_ics_link(base.http_get(PAGE_URL), PAGE_URL)
    if not ics_url:
        raise ValueError("no .ics link found on TAS term-dates page")
    # The TAS feed lists term periods; convert consecutive terms into the breaks.
    terms = base.events_from_ics(base.http_get(ics_url), "TAS", years)
    term_ranges = sorted((e.start, e.end) for e in terms)
    return base.breaks_from_terms(term_ranges, "TAS")
