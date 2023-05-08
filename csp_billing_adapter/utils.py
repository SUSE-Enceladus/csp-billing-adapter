#
# Copyright 2023 SUSE LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""utils.py is part of csp-billing-adapter and provides utility functions"""
import datetime
from dateutil.relativedelta import relativedelta
from dateutil import parser
import logging

log = logging.getLogger('CSPBillingAdapter')


def get_now() -> datetime.datetime:
    """get current time"""
    now = datetime.datetime.now(datetime.timezone.utc)

    logging.debug("Now: %s", now)

    return now


def date_to_string(date: datetime.datetime) -> str:
    """convert date to string"""
    try:
        formatted_date = date.isoformat()
    except (AttributeError, ValueError) as exc:
        raise type(exc)(
            f"Invalid date passed to date_to_string(): {date}") from exc

    log.debug("%s formatted as: %s", date, formatted_date)

    return formatted_date


def string_to_date(timestamp: str) -> datetime.datetime:
    """convert string to date"""
    try:
        parsed_date = parser.parse(timestamp)
    except ValueError as exc:
        raise type(exc)(
            f"Invalid timestamp passed to string_to_date(): {timestamp}") \
            from exc

    log.debug("%s parsed to: %s", repr(timestamp), parsed_date)

    return parsed_date


def get_date_delta(
    date: datetime.datetime,
    delta: int
) -> datetime.datetime:
    """get a new date using a provided date and delta offset"""
    try:
        date_delta = date + datetime.timedelta(seconds=delta)
    except TypeError as exc:
        raise type(exc)(
            f"Invalid values passed to get_date_delta() "
            f"date:{date} delta:{delta}"
            ) from exc

    log.debug(
        "%s + %d seconds: %s",
        date,
        delta,
        date_delta
    )

    return date_delta


def get_relative_period_delta(billing_interval: str):
    """
    Determine the relative period delta for the specified periodicity.
    """
    kwargs = {}

    if billing_interval == 'monthly':
        kwargs['months'] = 1
    elif billing_interval == 'hourly':
        kwargs['hours'] = 1
    elif billing_interval == 'test':
        kwargs['minutes'] = 5

    return relativedelta(**kwargs)


def get_next_bill_time(
    date: datetime.datetime,
    billing_interval: str
) -> datetime.datetime:
    """
    Determine the next billing date using provided date and billing interval
    """
    bill_time = date + get_relative_period_delta(billing_interval)

    log.debug(
        "Next %s bill time after %s: %s",
        date,
        billing_interval,
        bill_time
    )

    return bill_time


def get_prev_bill_time(
    date: datetime.datetime,
    billing_interval: str
) -> datetime.datetime:
    """
    Determine the prev billing date using provided date and billing interval
    """
    bill_time = date - get_relative_period_delta(billing_interval)

    log.debug(
        "Previous %s bill time before %s: %s",
        date,
        billing_interval,
        bill_time
    )

    return bill_time
