# Spec: Vietnamese Business-Day Calendar

| Field | Value |
|---|---|
| **Status** | ACCEPTED |
| **Owner** | Edward |
| **Implementer(s)** | Edward (backend) |
| **Module** | `app/repayment_schedule/calendar.py` |
| **Version** | 1.0 |
| **Date** | 2026-09-17 |
| **Related ADR** | — |
| **Depends on** | — |

---

## 1. Context & Goal

HANDOFF-03 Issue 9 (OP-05): `N0`, `N_bs` and every `scheduled_date` depend
on a Vietnamese public-holiday calendar including Tết, which EC-01
forbids deriving from weekday rules -- Tết alone removes 1-2 weeks. This
was flagged as a data problem needing an owner (T0d: "Supply the Vietnamese
business-day calendar for 2026-2027 including Tết," owner: Ops).

**Goal:** a maintained annual holiday table plus a calendar service that
T7 (schedule generation) and T9/T11 (backstop date recomputation) can call,
which fails loudly rather than silently assuming a year has no holidays.

**On the T0d ownership question:** this handoff could not wait on an Ops
sign-off cycle without blocking T7, so the 2026 dates were sourced and
cross-checked against Vietnam's Ministry of Home Affairs' official 2026
holiday-schedule announcement and independent corroborating sources (see
Open Questions for links); 2027 is explicitly marked `provisional` in the
data file pending the government's actual announcement (typically Q4 of
the preceding year). Ops should review both years before this governs real
facility data, and 2027 must be reconfirmed regardless.

---

## 2. Out of Scope

- Per-SME or per-province calendar customization -- the `extra_holidays`
  constructor parameter is the seam for it, but nothing populates it today;
  every facility uses the same national calendar.
- Compensatory workday swaps the government sometimes announces (e.g. "a
  Saturday becomes a working day to make up for a mid-week bridge") --
  those affect state-employee scheduling, not which days count as
  "business days" for computing a daily repayment amount, and are not
  modeled here.
- Years beyond 2027.

---

## 3. Data Model

No database table. Holiday data lives in
`app/repayment_schedule/data/vn_public_holidays.yaml`, keyed by year, each
year carrying a `status` (`confirmed` | `provisional`) and a list of
`{date, name}` holiday entries. Only statutory holidays that fall on a
weekday are listed -- a holiday that falls on a weekend is already excluded
by the ordinary Mon-Fri rule and is deliberately omitted to avoid drift.
Where the government moves an observance to a different weekday (e.g.
Hùng Kings' Commemoration Day 2026, whose traditional date is a Sunday),
the *observed* weekday is listed, not the traditional date.

---

## 4. API Contract

Not an HTTP surface. The contract is the Python API:

```python
class BusinessDayCalendar:
    def __init__(self, extra_holidays: frozenset[date] | None = None): ...
    def is_business_day(self, d: date) -> bool: ...
    def generate_business_days(self, start_date: date, count: int) -> list[date]: ...
    def nth_business_day(self, start_date: date, n: int) -> date: ...
    def recompute_backstop_date(self, start_date: date, backstop_day_index: int) -> date: ...

def known_calendar_years() -> frozenset[int]: ...
def calendar_year_status(year: int) -> str | None: ...
```

---

## 5. State Machine

Not applicable.

---

## 6. Business Rules

1. A business day is Monday-Friday and not a listed public holiday
   (EC-01) -- weekday rules alone are never sufficient.
2. `is_business_day()` raises `MissingHolidayCalendarYearError` for any
   year with no entry in the data file at all, rather than silently
   treating an unmaintained year as holiday-free.
3. `generate_business_days()` never produces a placeholder or a shifted
   amount for a non-business day -- it simply does not count that day
   (EC-01); a schedule spanning Tết extends in calendar terms, consuming
   no extra schedule slot and triggering no extension event.
4. `backstop_date` is always derived from `backstop_day_index` via
   `recompute_backstop_date()` -- never stored as the source of truth and
   never computed by any other path. A calendar revision (a newly
   announced holiday) changes the date a given index lands on; it never
   changes the index itself (EC-15) -- that immutability is enforced at
   the DB layer in T6, not by this module.

---

## 7. Error Cases

| Scenario | System behaviour | Response to caller |
|---|---|---|
| Calendar year has no entry in `vn_public_holidays.yaml` | `MissingHolidayCalendarYearError` | — (Python exception; callers must not catch-and-ignore) |
| `generate_business_days(count=0)` or negative | `ValueError` | — |
| Holiday-data bug causes an unbounded scan (e.g. every day misclassified as a holiday) | `RuntimeError` after a bounded scan, rather than an infinite loop | — |

---

## 8. Acceptance Criteria

- [x] `test_tet_2026_is_excluded_even_though_all_weekdays`
- [x] `test_schedule_spanning_tet_extends_with_no_gap_and_no_extension_event`
- [x] `test_backstop_date_is_recomputable_and_index_is_not_encoded_in_it` -- EC-15
- [x] `test_unknown_year_raises_loudly_rather_than_assuming_no_holidays`
- [x] `test_2026_is_confirmed_and_2027_is_provisional`

---

## 9. Open Questions

| # | Question | Owner | Resolution |
|---|---|---|---|
| 1 | 2027's exact holiday schedule is not yet officially published by the Vietnamese government as of this handoff (2026-09-17). | Ops (T0d) | Data file marks 2027 `status: provisional`; `calendar_year_status()` exposes this so a caller can warn/gate on it. Reconfirm against the official announcement once published (typically Q4 2026). |
| 2 | Should per-province holidays ever apply (some provinces observe additional local days)? | Ops | Not raised in HANDOFF-03; `extra_holidays` is the seam if it ever is. |

Sources consulted for the 2026/2027 dates in the data file: Vietnam's
Ministry of Home Affairs 2026 announcement (via baochinhphu.vn, the
government's official English-language news portal), vietnam-briefing.com,
and myvietnamvisa.com (cross-checked for 2027).

---

## Changelog

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-09-17 | Edward | Initial calendar service and 2026/2027 data (T8, HANDOFF-03). |
