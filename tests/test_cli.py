import pytest

from config.settings import MIN_RUN_SIZE
from main import _parse_args


def test_min_run_defaults_to_settings():
    args = _parse_args([])
    assert args.min_run == MIN_RUN_SIZE


def test_min_run_can_be_overridden():
    args = _parse_args(["--min-run", "8"])
    assert args.min_run == 8


def test_min_run_requires_positive_value():
    with pytest.raises(SystemExit):
        _parse_args(["--min-run", "0"])


def test_refresh_defaults_to_false():
    args = _parse_args([])
    assert args.refresh is False


def test_refresh_can_be_enabled():
    args = _parse_args(["--refresh"])
    assert args.refresh is True


def test_verbose_defaults_to_false():
    args = _parse_args([])
    assert args.verbose is False


def test_verbose_can_be_enabled():
    args = _parse_args(["--verbose"])
    assert args.verbose is True


def test_workers_defaults_to_forty():
    args = _parse_args([])
    assert args.workers == 40


def test_workers_can_be_overridden():
    args = _parse_args(["--workers", "5"])
    assert args.workers == 5


def test_workers_requires_positive_value():
    with pytest.raises(SystemExit):
        _parse_args(["--workers", "0"])
