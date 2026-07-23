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

    # The TAS feed lists term time in weekly fragments (each summarised
    # "Term N ..."), not one event per term. Coalesce contiguous fragments back
    # into whole terms first; otherwise breaks_from_terms() treats every
    # weekend *between* weeks as a school-holiday break.
    fragments = sorted({(event.start, event.end) for event in terms})
    term_ranges = base.coalesce_ranges(fragments)

    # After coalescing we expect ~4 whole terms per fully-covered year. School
    # feeds only reach ~1-2 years out, so require at least one full year of
    # terms; fewer means the scrape is broken and resolve() should fall back to
    # the last-known-good cache rather than publish bad breaks.
    if len(term_ranges) < 4:
        raise ValueError(
            f"TAS feed yielded only {len(term_ranges)} whole terms "
            f"(from {len(fragments)} fragments); expected at least 4"
        )

    return base.breaks_from_terms(term_ranges, "TAS")
