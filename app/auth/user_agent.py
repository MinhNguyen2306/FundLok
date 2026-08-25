"""Turn a raw User-Agent string into something a person can recognise.

The security screen asks a user to decide whether a signed-in device is theirs.
"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 …" does not
help them answer that; "MacBook Pro · Chrome 141" does.

This is deliberately a small, dependency-free heuristic rather than a UA-parsing
library: the output is a label on a card, a wrong guess costs a slightly odd
device name, and the raw string stays in the database either way. Order matters
in both tables below — Edge and Chrome both claim "Chrome", and every browser
claims "Mozilla".
"""
from __future__ import annotations

import re

UNKNOWN_DEVICE = "Unknown device"
UNKNOWN_BROWSER = "Unknown browser"

# Checked in order; first match wins.
_DEVICES: tuple[tuple[str, str], ...] = (
    ("iPhone", "iPhone"),
    ("iPad", "iPad"),
    ("Android", "Android device"),
    ("Macintosh", "Mac"),
    ("Windows NT 10.0", "Windows PC"),
    ("Windows", "Windows PC"),
    ("CrOS", "Chromebook"),
    ("Linux", "Linux PC"),
)

# Edge and Opera embed "Chrome"; Chrome embeds "Safari". Most specific first.
_BROWSERS: tuple[tuple[str, str], ...] = (
    ("Edg", "Edge"),
    ("OPR", "Opera"),
    ("Chrome", "Chrome"),
    ("Firefox", "Firefox"),
    ("Safari", "Safari"),
)

_VERSION = {
    "Edge": r"Edg(?:e|A|iOS)?/(\d+)",
    "Opera": r"OPR/(\d+)",
    "Chrome": r"Chrome/(\d+)",
    "Firefox": r"Firefox/(\d+)",
    "Safari": r"Version/(\d+)",
}


def describe_device(user_agent: str | None) -> str:
    if not user_agent:
        return UNKNOWN_DEVICE
    for needle, label in _DEVICES:
        if needle in user_agent:
            return label
    return UNKNOWN_DEVICE


def describe_browser(user_agent: str | None) -> str:
    if not user_agent:
        return UNKNOWN_BROWSER
    for needle, label in _BROWSERS:
        if needle in user_agent:
            match = re.search(_VERSION[label], user_agent)
            # Mobile Safari reports no "Version/" on some builds; the name
            # alone is still useful, so the version is optional.
            return f"{label} {match.group(1)}" if match else label
    return UNKNOWN_BROWSER
