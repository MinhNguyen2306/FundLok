"""Curve primitives: sigmoid, linear, cubic.

Spec: docs/specs/underwriting/grading-engine-core.md, R2.

    score = min(100, max(0, upper / (1 + exp(sign * (steepness * x - intercept)))))
        sign = +1  when decreasing: true    (higher raw value = worse)
        sign = -1  when decreasing: false   (higher raw value = better)

`intercept` is NOT a midpoint. The true midpoint is `intercept / steepness`.
The requirements PDF labelled this column "Midpoint" and put the intercept
value in it, which made six factors look broken when they were not (see
deviations register D1). Do not "correct" this by substituting a midpoint
form -- these constants are fit to this exact form.
"""
from __future__ import annotations

import math

__all__ = ["clamp", "sigmoid", "linear", "cubic"]


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return min(high, max(low, value))


def sigmoid(x: float, *, upper: float, steepness: float, intercept: float, decreasing: bool) -> float:
    """`upper` is allowed to exceed 100 (several production factors do, up to
    168.6 -- curve-fit artifacts). The clamp below is what keeps the final
    score in [0, 100]; do not "fix" an `upper` > 100 in the params file."""
    sign = 1.0 if decreasing else -1.0
    exponent = sign * (steepness * x - intercept)
    try:
        denominator = 1.0 + math.exp(exponent)
    except OverflowError:
        # exponent so large that exp() overflows a double -- the curve has
        # already saturated; math.inf denominator drives the score to 0.
        denominator = math.inf
    raw = 0.0 if math.isinf(denominator) else upper / denominator
    return clamp(raw)


def linear(x: float, *, formula: str = "100 - x") -> float:
    """Both Top 1 and Top 3 concentration use this in production (the
    requirements PDF's Top 3 sigmoid is not what the workbook's production
    column computes -- see deviations register D5). Only the one formula the
    params file actually uses is implemented; an unrecognised formula string
    is a params/code drift and should fail loudly rather than guess."""
    if formula != "100 - x":
        raise ValueError(f"Unsupported linear formula: {formula!r}")
    return clamp(100.0 - x)


def cubic(x: float, *, a: float, b: float, c: float, d: float) -> float:
    """score = min(100, max(0, a*x^3 + b*x^2 + c*x + d)). Used for Owner
    Withdrawal when its raw input is the 0-1 ratio the params file models
    (see deviations register D22 for why factors.py does not currently wire
    the fixture's input through this)."""
    raw = a * x**3 + b * x**2 + c * x + d
    return clamp(raw)
