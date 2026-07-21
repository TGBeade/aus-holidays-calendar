"""Turn HolidayEvent lists into subscribable .ics calendars."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from icalendar import Calendar, Event

from . import config
from .models import HolidayEvent

_STAMP = datetime.strptime(config.GENERATED_STAMP, "%Y%m%dT%H%M%SZ").replace(
    tzinfo=timezone.utc
)


def _build_calendar(name: str, events: list[HolidayEvent]) -> Calendar:
    cal = Calendar()
    cal.add("prodid", config.PRODID)
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("method", "PUBLISH")
    cal.add("x-wr-calname", name)
    cal.add("x-wr-timezone", config.TIMEZONE)
    cal.add("x-published-ttl", config.PUBLISHED_TTL)
    cal.add(
        "refresh-interval",
        timedelta(days=1),
        parameters={"VALUE": "DURATION"},
    )

    for ev in sorted(events, key=lambda e: (e.start, e.state, e.summary)):
        item = Event()
        item.add("summary", ev.title)
        item.add("dtstart", ev.start)                       # VALUE=DATE (all-day)
        item.add("dtend", ev.end + timedelta(days=1))       # DTEND is exclusive
        item.add("dtstamp", _STAMP)
        item["uid"] = ev.uid
        item.add("transp", "TRANSPARENT")                   # don't block free/busy
        item.add("categories", [ev.category, ev.state])
        cal.add_component(item)
    return cal


def write(path: str | Path, name: str, events: list[HolidayEvent]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_build_calendar(name, events).to_ical())
