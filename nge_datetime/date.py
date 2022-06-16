import time
import datetime

ISO_8601_format_DT: str = "%Y-%m-%dT%H:%M:%S%z"
ISO_8601_format_D: str = "%Y-%m-%d"


def get_dates_between(date_1: datetime.date,
                      date_2: datetime.date):
    date_delta: datetime.timedelta = date_1 - date_2
    days_delta: int = date_delta.days

    dates: [datetime.date] = []

    if days_delta > 0:
        for i in range(0, days_delta + 1, 1):
            day: datetime.date = date_1 - datetime.timedelta(i)
            dates.append(day)
    elif days_delta < 0:
        for i in range(0, days_delta - 1, -1):
            day: datetime.date = date_1 - datetime.timedelta(i)
            dates.append(day)

    return dates
