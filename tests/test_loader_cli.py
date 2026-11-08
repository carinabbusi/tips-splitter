from decimal import Decimal
from pathlib import Path

import pytest

from tips_splitter.cli import main
from tips_splitter.loader import load_entries
from tips_splitter.splitter import TipSplitError

SAMPLE = Path(__file__).parent.parent / "data" / "sample_tips.csv"


def test_load_sample_file():
    entries = load_entries(SAMPLE)
    assert len(entries) > 0
    assert all(e.amount >= Decimal("0") for e in entries)


def test_missing_column(tmp_path):
    bad = tmp_path / "bad.csv"
    bad.write_text("date,amount\n2026-09-01,10.00\n", encoding="utf-8")
    with pytest.raises(TipSplitError, match="workers"):
        load_entries(bad)


def test_invalid_date(tmp_path):
    bad = tmp_path / "bad.csv"
    bad.write_text("date,amount,workers\n01/09/2026,10.00,Alex\n", encoding="utf-8")
    with pytest.raises(TipSplitError, match="Line 2"):
        load_entries(bad)


def test_cli_prints_summary(capsys):
    assert main([str(SAMPLE)]) == 0
    out = capsys.readouterr().out
    assert "Total collected" in out


def test_cli_missing_file_returns_error(capsys):
    assert main(["does-not-exist.csv"]) == 1
    assert "Error" in capsys.readouterr().err
