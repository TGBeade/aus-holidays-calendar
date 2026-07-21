"""Australian Capital Territory school holidays — parsed from a public per-year site.

ACT's official department page (education.act.gov.au) is Cloudflare-blocked from
any server (including GitHub Actions), so we read term dates from this public
per-year site instead. Each page has a "Term N | start | end" table with full
dates (the start cell may list new- and continuing-student dates; the parser
uses the later one); base.breaks_from_term_pages collects the terms across a run
of yearly pages and derives the between-term breaks. Verified 2026 dates are
seeded in data/seed/act.csv as the safety net.
"""

from .. import config
from ..models import HolidayEvent
from . import base

SOURCE_TEMPLATE = "https://schoolholidaysact.com.au/act-school-holidays-{year}/"


def fetch(years: range) -> list[HolidayEvent]:
    scan = range(config.SCHOOL_START_YEAR, config.PUBLIC_END_YEAR + 1)
    return base.breaks_from_term_pages(SOURCE_TEMPLATE, "ACT", scan)
