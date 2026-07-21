"""Public holidays for all states/territories via the `holidays` library.

Rule-based, so it computes any future year on the fly -- no scraping, and no
"only published two years ahead" ceiling.

A holiday observed on the SAME date with the SAME name in all eight
jurisdictions is emitted once as a single [National] event. Everything else
(King's Birthday, Labour Day, show days, etc., which fall on different dates in
different states) is emitted per state.
"""

from __future__ import annotations

from collections import defaultdict

import holidays

from . import config
from .models import HolidayEvent


def collect(start_year: int | None = None, end_year: int | None = None) -> list[HolidayEvent]:
    start_year = start_year or config.PUBLIC_START_YEAR
    end_year = end_year or config.PUBLIC_END_YEAR
    years = range(start_year, end_year + 1)

    # (date, name) -> set of states observing it that day.
    grouped: dict[tuple, set[str]] = defaultdict(set)
    for state in config.STATES:
        cal = holidays.country_holidays("AU", subdiv=state, years=years)
        for day, name in cal.items():
            grouped[(day, name)].add(state)

    all_states = set(config.STATES)
    events: list[HolidayEvent] = []
    for (day, name), states in grouped.items():
        if states == all_states:
            events.append(
                HolidayEvent(config.NATIONAL, name, day, day, "public")
            )
        else:
            for state in sorted(states):
                events.append(HolidayEvent(state, name, day, day, "public"))

    events.sort(key=lambda e: (e.start, e.state, e.summary))
    return events
