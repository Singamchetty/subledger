import calendar
from datetime import date

CYCLE_MONTHS = {"monthly": 1, "quarterly": 3, "yearly": 12}


def add_cycle(start: date, billing_cycle: str) -> date:
    """Return the start of the next period (the exclusive end of this one)."""
    months = CYCLE_MONTHS[billing_cycle]
    index = start.year * 12 + (start.month - 1) + months
    year, month = divmod(index, 12)
    month += 1
    day = min(start.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)
