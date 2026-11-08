from datetime import date
from decimal import Decimal

import pytest

from tips_splitter.splitter import (
    TipEntry,
    TipSplitError,
    normalize_name,
    split_amount,
    split_period,
    to_cents,
)


def test_even_split():
    assert split_amount("30.00", ["Alex", "Bia", "Caio"]) == {
        "Alex": Decimal("10.00"),
        "Bia": Decimal("10.00"),
        "Caio": Decimal("10.00"),
    }


def test_leftover_cents_go_alphabetically_and_sum_matches():
    shares = split_amount("10.00", ["Caio", "Alex", "Bia"])
    assert shares == {"Alex": Decimal("3.34"), "Bia": Decimal("3.33"), "Caio": Decimal("3.33")}
    assert sum(shares.values()) == Decimal("10.00")


@pytest.mark.parametrize("amount", ["0.01", "0.05", "1.00", "17.23", "99.99", "1234.57"])
@pytest.mark.parametrize("people", [1, 2, 3, 4, 6, 7])
def test_shares_always_add_up_to_total(amount, people):
    workers = [f"Person {i}" for i in range(people)]
    shares = split_amount(amount, workers)
    assert sum(shares.values()) == Decimal(amount)
    assert max(shares.values()) - min(shares.values()) <= Decimal("0.01")


def test_single_worker_gets_everything():
    assert split_amount("12.40", ["Alex"]) == {"Alex": Decimal("12.40")}


def test_zero_tips_day():
    assert split_amount("0", ["Alex", "Bia"]) == {"Alex": Decimal("0.00"), "Bia": Decimal("0.00")}


def test_names_are_normalized_and_deduplicated():
    shares = split_amount("20.00", ["  bia ", "BIA", "alex"])
    assert shares == {"Alex": Decimal("10.00"), "Bia": Decimal("10.00")}


def test_normalize_name():
    assert normalize_name("  ana   maria ") == "Ana Maria"


@pytest.mark.parametrize("bad", ["-1", "abc", "1.234", "NaN"])
def test_invalid_amounts_are_rejected(bad):
    with pytest.raises(TipSplitError):
        to_cents(bad)


def test_no_workers_is_rejected():
    with pytest.raises(TipSplitError):
        split_amount("10.00", [])


def test_blank_worker_name_is_rejected():
    with pytest.raises(TipSplitError):
        split_amount("10.00", ["Alex", "   "])


def test_split_period_totals_and_days():
    entries = [
        TipEntry(date(2026, 9, 2), Decimal("20.00"), ("Alex", "Bia")),
        TipEntry(date(2026, 9, 1), Decimal("30.00"), ("Alex", "Bia", "Caio")),
        TipEntry(date(2026, 9, 3), Decimal("5.00"), ("Caio",)),
    ]
    report = split_period(entries)

    assert report.total == Decimal("55.00")
    assert report.per_person == {
        "Alex": Decimal("20.00"),
        "Bia": Decimal("20.00"),
        "Caio": Decimal("15.00"),
    }
    assert report.days_worked == {"Alex": 2, "Bia": 2, "Caio": 2}
    assert [d.day for d in report.days] == [date(2026, 9, 1), date(2026, 9, 2), date(2026, 9, 3)]
    assert sum(report.per_person.values()) == report.total


def test_split_period_requires_entries():
    with pytest.raises(TipSplitError):
        split_period([])
