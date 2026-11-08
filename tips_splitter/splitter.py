"""Core business rules for splitting tips.

Rule: each day's tips are split equally among everyone who worked that day.
All maths is done in integer cents so the shares always add up to the
exact amount collected. Leftover cents (e.g. EUR 10.00 / 3) are handed out
one at a time in alphabetical order, so the result is fair and repeatable.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation

CENT = Decimal("0.01")


class TipSplitError(ValueError):
    """Raised when a tip entry is invalid."""


def normalize_name(name: str) -> str:
    """Trim extra spaces and use title case: '  ana  maria ' -> 'Ana Maria'."""
    cleaned = " ".join(str(name).split())
    if not cleaned:
        raise TipSplitError("Worker name cannot be empty")
    return cleaned.title()


def to_cents(amount: Decimal | str | int | float) -> int:
    """Convert a euro amount to integer cents, rejecting bad values."""
    try:
        value = Decimal(str(amount))
    except InvalidOperation as exc:
        raise TipSplitError(f"Invalid amount: {amount!r}") from exc
    if not value.is_finite():
        raise TipSplitError(f"Invalid amount: {amount!r}")
    if value < 0:
        raise TipSplitError("Amount cannot be negative")
    if value != value.quantize(CENT):
        raise TipSplitError("Amount cannot have more than 2 decimal places")
    return int(value * 100)


def from_cents(cents: int) -> Decimal:
    return (Decimal(cents) / 100).quantize(CENT)


def split_amount(amount: Decimal | str | int | float, workers: list[str]) -> dict[str, Decimal]:
    """Split one amount equally among workers. Shares always sum to the amount."""
    names = sorted({normalize_name(w) for w in workers})
    if not names:
        raise TipSplitError("At least one worker is required")

    total_cents = to_cents(amount)
    base, remainder = divmod(total_cents, len(names))
    return {name: from_cents(base + (1 if index < remainder else 0)) for index, name in enumerate(names)}


@dataclass(frozen=True)
class TipEntry:
    day: date
    amount: Decimal
    workers: tuple[str, ...]


@dataclass
class DayBreakdown:
    day: date
    amount: Decimal
    shares: dict[str, Decimal]


@dataclass
class SplitReport:
    total: Decimal = Decimal("0.00")
    per_person: dict[str, Decimal] = field(default_factory=dict)
    days_worked: dict[str, int] = field(default_factory=dict)
    days: list[DayBreakdown] = field(default_factory=list)


def split_period(entries: list[TipEntry]) -> SplitReport:
    """Split a whole period (e.g. a month). Entries on the same day are kept separate."""
    if not entries:
        raise TipSplitError("No tip entries provided")

    totals: dict[str, int] = defaultdict(int)
    days_worked: dict[str, set[date]] = defaultdict(set)
    breakdown: list[DayBreakdown] = []
    grand_total = 0

    for entry in sorted(entries, key=lambda e: e.day):
        shares = split_amount(entry.amount, list(entry.workers))
        grand_total += to_cents(entry.amount)
        for name, share in shares.items():
            totals[name] += to_cents(share)
            days_worked[name].add(entry.day)
        breakdown.append(
            DayBreakdown(day=entry.day, amount=from_cents(to_cents(entry.amount)), shares=shares)
        )

    return SplitReport(
        total=from_cents(grand_total),
        per_person={name: from_cents(c) for name, c in sorted(totals.items())},
        days_worked={name: len(d) for name, d in sorted(days_worked.items())},
        days=breakdown,
    )
