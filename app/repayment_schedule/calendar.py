"""Vietnamese business-day calendar (T8, HANDOFF-03 Issue 9 / OP-05).

N0, N_bs and every `scheduled_date` (spec §4.1/§8) depend on a Vietnamese
public-holiday calendar including Tết, which EC-01 forbids deriving from
weekday rules -- Tết alone removes 1-2 weeks. The holiday data itself lives
in `app/repayment_schedule/data/vn_public_holidays.yaml` (a maintained
annual table, per T8) and is loaded here; this module is the calendar
*service* T7/T9/T11 call, not the data.

"Per-SME calendar" (T8): the constructor accepts optional per-caller extra
holiday dates so a future province-specific or SME-specific observance can
be layered on without changing this module -- today nothing supplies any,
so every facility uses the shared national calendar.
"""
from __future__ import annotations

import datetime
from functools import lru_cache
from pathlib import Path

import yaml

DEFAULT_WORKING_DAYS_PER_MONTH = 22  # T5 -- matches pricing.py's params_version bump to 22

_DATA_PATH = Path(__file__).parent / "data" / "vn_public_holidays.yaml"


class MissingHolidayCalendarYearError(Exception):
    """Raised when the calendar is asked about a year with no entry in
    vn_public_holidays.yaml at all. A year silently treated as "all
    weekdays are business days" would misprice every schedule spanning
    Tết in that year -- this fails loudly instead (per the handoff's
    instruction that every invariant fails loudly rather than continuing
    with inconsistent state)."""


@lru_cache(maxsize=1)
def _load_holiday_calendar() -> dict[int, dict]:
    """Parse vn_public_holidays.yaml once per process. Returns
    {year: {"status": "confirmed"|"provisional", "dates": frozenset[date]}}.
    """
    with open(_DATA_PATH, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    result: dict[int, dict] = {}
    for year, year_data in raw.get("years", {}).items():
        dates = frozenset(entry["date"] for entry in year_data.get("holidays", []))
        result[int(year)] = {"status": year_data.get("status", "confirmed"), "dates": dates}
    return result


def known_calendar_years() -> frozenset[int]:
    return frozenset(_load_holiday_calendar().keys())


def calendar_year_status(year: int) -> str | None:
    """Returns "confirmed", "provisional", or None if the year has no
    entry at all."""
    entry = _load_holiday_calendar().get(year)
    return entry["status"] if entry else None


class BusinessDayCalendar:
    """Per-SME business-day calendar (T8). Today every instance uses the
    same national VN holiday table; `extra_holidays` is the seam for a
    future per-SME/per-province override.
    """

    def __init__(self, extra_holidays: frozenset[datetime.date] | None = None):
        self._extra_holidays = extra_holidays or frozenset()

    def _year_is_known(self, year: int) -> bool:
        return year in known_calendar_years()

    def _is_holiday(self, d: datetime.date) -> bool:
        if d in self._extra_holidays:
            return True
        calendar = _load_holiday_calendar()
        year_entry = calendar.get(d.year)
        return year_entry is not None and d in year_entry["dates"]

    def is_business_day(self, d: datetime.date) -> bool:
        """A business day is Mon-Fri and not a public holiday (EC-01).
        Raises MissingHolidayCalendarYearError if `d.year` has no entry in
        the holiday table at all -- rather than silently assuming no
        holidays exist that year.
        """
        if not self._year_is_known(d.year):
            raise MissingHolidayCalendarYearError(
                f"No holiday calendar entry for {d.year} in {_DATA_PATH.name}. "
                "A schedule cannot be generated into a year with no maintained "
                "holiday table (OP-05) -- add it before proceeding."
            )
        return d.weekday() < 5 and not self._is_holiday(d)

    def generate_business_days(self, start_date: datetime.date, count: int) -> list[datetime.date]:
        """The first `count` business days on or after `start_date`,
        inclusive of `start_date` itself if it is a business day. Non-
        business days (weekends, holidays) generate no slot and are simply
        skipped (EC-01) -- never a placeholder, never a shifted amount."""
        if count <= 0:
            raise ValueError(f"count must be positive, got {count}")
        dates: list[datetime.date] = []
        d = start_date
        # Bounded iteration guard: at ~5 business days/week this is at most
        # ~10x count calendar days for any realistic holiday density; a
        # runaway (e.g. a bug leaving _is_holiday always True) fails loudly
        # rather than looping forever.
        max_calendar_days = count * 10 + 366
        scanned = 0
        while len(dates) < count:
            if scanned > max_calendar_days:
                raise RuntimeError(
                    f"generate_business_days scanned {scanned} calendar days without finding "
                    f"{count} business days starting from {start_date} -- likely a holiday-data bug"
                )
            if self.is_business_day(d):
                dates.append(d)
            d += datetime.timedelta(days=1)
            scanned += 1
        return dates

    def nth_business_day(self, start_date: datetime.date, n: int) -> datetime.date:
        """The date of the nth business day (1-indexed), counting from
        `start_date` inclusive. Used to derive `backstop_date` from the
        immutable `backstop_day_index` (EC-15) -- recomputable at any time
        from the calendar, independent of the index itself."""
        return self.generate_business_days(start_date, n)[-1]

    def recompute_backstop_date(self, start_date: datetime.date, backstop_day_index: int) -> datetime.date:
        """`backstop_date` is derived and recomputable (EC-15): a calendar
        revision (e.g. a newly announced holiday) changes the *date* a
        given `backstop_day_index` lands on, but never the index itself --
        that stays immutable at the DB layer (INV-10, T6)."""
        return self.nth_business_day(start_date, backstop_day_index)
