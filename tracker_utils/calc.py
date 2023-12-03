from datetime import datetime, timezone, timedelta
from typing import Literal
from decimal import Decimal
import pytz

CUR_WEEK = "cw"
PREV_WEEK = "pw"
CUR_MONTH = "cm"
PREV_MONTH = "pm"
PERIODS = Literal["cw", "pw", "cm", "pm"]


# transforms predefined periods to datetime
def period_to_dates(period: PERIODS) -> tuple[datetime, datetime]:
    """Transform Period to datetime"""
    today = datetime.now(tz=timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    if period == CUR_WEEK:
        shift = today.weekday()
        start_date = today - timedelta(days=shift)
        end_date = None
    elif period == PREV_WEEK:
        shift = today.weekday() + 7
        start_date = today - timedelta(days=shift)
        end_date = start_date + timedelta(days=7)
    elif period == CUR_MONTH:
        start_date = today.replace(day=1)
        end_date = None
    elif period == PREV_MONTH:
        if today.month == 1:
            year = today.year - 1
            month = 12
        else:
            year = today.year
            month = today.month - 1
        start_date = today.replace(year=year, month=month, day=1)
        end_date = today.replace(day=1)
    else:
        start_date, end_date = None, None

    return start_date, end_date


# calculate cumulative profit
def cumulate_profit(data: list[Decimal]) -> list[Decimal]:
    """transform profit to cumulative profit (next=current + sum(previous))"""
    cumulative_values = []
    cumulative_sum = 0
    for value in data:
        cumulative_sum += value
        cumulative_values.append(cumulative_sum)
    return cumulative_values


# split list of tuples to several list for each week
def sum_by_weeks(data: list[tuple[datetime, Decimal]]) -> dict[Decimal]:
    """Split and sum data by week. Returns dict where key=#week value=sum(values in this week)"""
    result = {}
    for item in data:
        date = item[0].astimezone(tz=pytz.utc)
        year, week, _ = date.isocalendar()
        week = f"0{week}" if week < 10 else str(week)
        key = f"{year}-{week}"
        result[key] = result.get(key, 0) + item[1]
    return dict(sorted(result.items()))


# split list of tuples to several list for each week
def sum_by_month(data: list[tuple[datetime, Decimal]]) -> dict[Decimal]:
    """Split and sum data by month. Returns dict where key=#month value=sum(values in this month)"""
    result = {}
    for item in data:
        date = item[0].astimezone(tz=pytz.utc)
        month = f"0{date.month}" if date.month < 10 else str(date.month)
        key = f"{date.year}-{month}"
        result[key] = result.get(key, 0) + item[1]
    return dict(sorted(result.items()))
