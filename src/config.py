"""Central configuration for the Australian holidays calendar builder."""

from datetime import date

# All eight Australian states/territories (holidays library subdiv codes).
STATES = ["ACT", "NSW", "NT", "QLD", "SA", "TAS", "VIC", "WA"]

# Label used when a public holiday is observed on the same date in every
# state/territory (i.e. a genuinely national holiday).
NATIONAL = "National"

# --- Year coverage -----------------------------------------------------------
# Public holidays are rule-based (computed on the fly) so we can project years
# ahead cheaply. School dates realistically only exist ~1-2 years out.
_THIS_YEAR = date.today().year
PUBLIC_START_YEAR = _THIS_YEAR
PUBLIC_END_YEAR = _THIS_YEAR + 5
SCHOOL_START_YEAR = _THIS_YEAR
SCHOOL_END_YEAR = _THIS_YEAR + 2

# --- ICS metadata ------------------------------------------------------------
# Used to build stable UIDs. Change the domain to your repo/org if you like;
# just keep it constant so calendar clients treat re-runs as updates, not new
# events.
UID_DOMAIN = "aus-holidays-calendar.github.io"

# Fixed DTSTAMP so identical holiday data produces byte-identical output. This
# keeps weekly CI commits clean (a diff only appears when dates actually change).
GENERATED_STAMP = "20240101T000000Z"

# Refresh hint for subscribing clients (Outlook/Apple/Google honour this loosely).
PUBLISHED_TTL = "P1D"

TIMEZONE = "Australia/Sydney"  # informational only; all events are all-day.

PRODID = "-//Therapeutic Guidelines//AU Holidays Calendar//EN"

# Output calendars -> (filename, human name).
CAL_ALL = ("all-states.ics", "Australian Holidays \u2014 All States")
CAL_PUBLIC = ("public-holidays.ics", "Australian Public Holidays \u2014 All States")
CAL_SCHOOL = ("school-holidays.ics", "Australian School Holidays \u2014 All States")

# Directory layout (relative to repo root).
DOCS_DIR = "docs"
BYSTATE_DIR = "docs/by-state"
CACHE_DIR = "data/cache"
SEED_DIR = "data/seed"
STATUS_FILE = "docs/status.json"
