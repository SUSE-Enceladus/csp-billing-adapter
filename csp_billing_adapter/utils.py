import datetime

from dateutil.relativedelta import relativedelta


def get_now():
    return datetime.datetime.now(datetime.timezone.utc)


def date_to_string(date):
    return date.isoformat()


def string_to_date(timestamp):
    return datetime.datetime.fromisoformat(timestamp)


def get_date_delta(date: datetime.datetime, delta: int):
    return date + datetime.timedelta(seconds=delta)


def get_next_bill_time(date: datetime.datetime, billing_interval: str):
    kwargs = {}

    if billing_interval == 'monthly':
        kwargs['months'] = 1
    elif billing_interval == 'hourly':
        kwargs['hours'] = 1

    return date + relativedelta(**kwargs)
