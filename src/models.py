"""Shared event model used by every data source."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

from . import config


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


@dataclass(frozen=True)
class HolidayEvent:
    """A single all-day (possibly multi-day) event.

    `start` and `end` are both INCLUSIVE calendar dates. `end == start` is a
    single day. The ICS writer converts `end` to the exclusive DTEND that
    iCalendar requires.
    """

    state: str          # one of config.STATES, or config.NATIONAL
    summary: str        # e.g. "Melbourne Cup Day" or "School holidays"
    start: date
    end: date
    category: str       # "public" or "school"

    @property
    def title(self) -> str:
        """Display title with a state prefix, e.g. '[VIC] Melbourne Cup Day'."""
        return f"[{self.state}] {self.summary}"

    @property
    def uid(self) -> str:
        """Stable, deterministic UID so re-runs update rather than duplicate."""
        key = (
            f"{self.category}-{self.state}-{_slug(self.summary)}"
            f"-{self.start:%Y%m%d}-{self.end:%Y%m%d}"
        )
        return f"{key}@{config.UID_DOMAIN}"
