from __future__ import annotations

from datetime import datetime, timedelta


MIN_INTERVAL_MINUTES = 15
MAX_INTERVAL_MINUTES = 60 * 24 * 30


def validate_interval(interval_minutes: int) -> int:
    if not MIN_INTERVAL_MINUTES <= interval_minutes <= MAX_INTERVAL_MINUTES:
        raise ValueError(
            f"L'intervalle doit être compris entre {MIN_INTERVAL_MINUTES} et {MAX_INTERVAL_MINUTES} minutes"
        )
    return interval_minutes


def next_run_at(moment: datetime, interval_minutes: int) -> datetime:
    return moment + timedelta(minutes=validate_interval(interval_minutes))
