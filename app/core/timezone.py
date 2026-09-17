"""Shared Vietnam timezone constant.

Repayment spec §14: "All timestamps Asia/Ho_Chi_Minh." Vietnam has used a
single UTC+7 offset with no daylight-saving transitions since 1975, so this
is safe to treat as a fixed, unambiguous zone across the whole app --
`state_transition`, ledger, and the daily batch (T2/T11) all anchor to it,
not to the host machine's local time or to UTC.
"""
from zoneinfo import ZoneInfo

ICT = ZoneInfo("Asia/Ho_Chi_Minh")
