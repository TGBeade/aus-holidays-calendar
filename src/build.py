"""Build all .ics calendars into docs/.

Run:  python -m src.build

Never crashes on a broken source -- each school source fails soft to its cache
or seed CSV, and the failure is recorded in docs/status.json (surfaced as a CI
warning by the workflow).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from . import config, ics_writer, public_holidays
from .models import HolidayEvent
from .school import act, base, nsw, nt, qld, sa, tas, vic, wa

# state code -> module exposing fetch(years)
SCHOOL_SOURCES = {
    "ACT": act, "NSW": nsw, "NT": nt, "QLD": qld,
    "SA": sa, "TAS": tas, "VIC": vic, "WA": wa,
}


def gather_school(status: dict) -> list[HolidayEvent]:
    years = range(config.SCHOOL_START_YEAR, config.SCHOOL_END_YEAR + 1)
    events: list[HolidayEvent] = []
    for state, module in SCHOOL_SOURCES.items():
        events.extend(base.resolve(state, module.fetch, years, status))
    return events


def _for_state(events: list[HolidayEvent], code: str) -> list[HolidayEvent]:
    return [e for e in events if e.state == code or e.state == config.NATIONAL]


def main() -> None:
    status: dict = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }

    public = public_holidays.collect()
    status["public"] = {"source": "holidays-lib", "count": len(public)}

    school_status: dict = {}
    school = gather_school(school_status)
    status["school"] = school_status

    everything = public + school

    # Primary + category calendars.
    ics_writer.write(Path(config.DOCS_DIR) / config.CAL_ALL[0], config.CAL_ALL[1], everything)
    ics_writer.write(Path(config.DOCS_DIR) / config.CAL_PUBLIC[0], config.CAL_PUBLIC[1], public)
    ics_writer.write(Path(config.DOCS_DIR) / config.CAL_SCHOOL[0], config.CAL_SCHOOL[1], school)

    # Per-state calendars (state-specific + national public holidays).
    for code in config.STATES:
        ics_writer.write(
            Path(config.BYSTATE_DIR) / f"{code}.ics",
            f"Australian Holidays \u2014 {code}",
            _for_state(everything, code),
        )

    Path(config.STATUS_FILE).write_text(json.dumps(status, indent=2))

    # Console summary.
    print(f"public holidays: {len(public)} events")
    for state, info in sorted(school_status.items()):
        flag = "" if info["source"] in ("live", "cache") else "  <-- CHECK"
        print(f"school {state}: {info['count']:>3} events via {info['source']}{flag}")
    degraded = [s for s, i in school_status.items() if i["source"] in ("seed", "none")]
    if degraded:
        print(f"\nWARNING: no live/cache data for: {', '.join(sorted(degraded))}")


if __name__ == "__main__":
    main()
