"""Tasmania school holidays.

TAS (Department for Education, Children and Young People) publishes an official
.ics linked from its term-dates page. The feed contains more than term ranges,
so only genuine Term 1-4 events are used to derive the between-term holidays.
"""

import re

from ..models import HolidayEvent
from . import base


PAGE_URL = "https://www.decyp.tas.gov.au/learning/term-dates/"
TERM_EVENT_RE = re.compile(r"^(?:TAS\s*[-:]\s*)?Term\s+[1-4]\b", re.IGNORECASE)


def fetch(years: range) -> list[HolidayEvent]:
    ics_url = base.find_ics_link(base.http_get(PAGE_URL), PAGE_URL)
    if not ics_url:
        raise ValueError("no .ics link found on TAS term-dates page")

    feed_events = base.events_from_ics(base.http_get(ics_url), "TAS", years)
    terms = [event for event in feed_events if TERM_EVENT_RE.match(event.summary)]
    term_ranges = sorted({(event.start, event.end) for event in terms})

    # Four terms per complete year are expected. Refuse suspicious feed data so
    # resolve() uses the last-known-good cache rather than publishing bad breaks.
    expected_minimum = 4 * len(years)
    if len(term_ranges) < expected_minimum:
        raise ValueError(
            f"TAS feed contained only {len(term_ranges)} term ranges; "
            f"expected at least {expected_minimum}"
        )

    return base.breaks_from_terms(term_ranges, "TAS")
