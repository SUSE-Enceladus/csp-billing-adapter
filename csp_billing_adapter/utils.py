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
import logging
import time

from dateutil.relativedelta import relativedelta
from dateutil import parser
from functools import partial

from csp_billing_adapter.config import Config


log = logging.getLogger('CSPBillingAdapter')


def get_now() -> datetime.datetime:
    """get current time"""
    now = datetime.datetime.now(datetime.timezone.utc)

    log.debug("Now: %s", now)

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
    elif billing_interval == 'daily':
        kwargs['days'] = 1
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


def retry_on_exception(
    func_call: partial,
    exceptions=Exception,
    retry_count: int = 3,
    retry_delay: float = 1,
    delay_factor: float = 1,
    logger: logging.Logger = None,
    func_name: str = None
):
    """
    Retry the provided function call that has been encapsulated using
    functools.partial as 'func_call', catching the given 'exceptions',
    up to 'retry_count' times, delaying by 'retry_delay' between tries,
    multiplied by 'delay_factor' after each attempt, logging retry
    status messages via 'log' if provided.

    :param func_call:
        The encapsulated function call that will be retried.
    :param exceptions:
        The exception, or tuple of exceptions, to catch and retry the
        func_call for.
    :param retry_count:
        The number of retries to attempt, after an initial failure,
        before raising any failure.
    :param retry_delay:
        The initial number of seconds to wait before retrying the
        func_call; will be multiplied after each attempt by the
        delay_factor. Can be a integer or float that is acceptable
        to time.sleep().
    :param delay_factor:
        The factory by which retry_delay will be multiplied after
        each retry attempt.
    :param logger:
        An optional Logger that, if specified, will be used to log
        retry status messages.
    :param func_name:
        An optional function name that will be used for logging
        purposes.

    :return:
        The result of calling func_call.
    """

    if logger is None:
        # if no specific logger was provided use default log
        logger = log

    if func_name is None:
        # if no function name is provided try using the name of
        # func_call.func, or failing that, 'unnamed_function'
        func_name = getattr(
            func_call.func,
            '__name__',
            'unnamed_function'
        )

    # ensure retry_count is a positive non-zero value, setting to 1 if not
    retries = abs(retry_count)
    if retries == 0:
        retries = 1
    if retries != retry_count:
        logger.debug(
            "Specified retry_count %d corrected to %d",
            retry_count,
            retries
        )

    # ensure retry_delay is a positive non-zero value, setting to 1 if not
    delay = abs(retry_delay)
    if delay == 0:
        delay = 1
    if delay != retry_delay:
        logger.debug(
            "Specified retry_delay %g corrected to %g",
            retry_delay,
            delay
        )

    # ensure delay_factor is a positive non-zero value, setting to 1 if not
    delay_mult = abs(delay_factor)
    if delay_mult == 0:
        delay_mult = 1
    if delay_mult != delay_factor:
        logger.debug(
            "Specified delay_factor %g corrected to %g",
            delay_factor,
            delay_mult
        )

    while True:
        try:
            logger.debug("Attempting to run '%s'", func_name)
            return func_call()
        except exceptions as error:
            logger.debug('%s: Caught exception: %s', func_name, str(error))

            # re-raise if no more retries left
            if retries == 0:
                logger.debug(
                    '%s: Retries exhausted, re-raising: %s',
                    func_name,
                    str(error)
                )
                raise

            logger.warning(
                "%s: %s, retry after %g second%s, %d attempt%s remaining...",
                func_name,
                str(error),
                delay,
                's' if delay != 1 else '',
                retries,
                's' if retries != 1 else ''
            )

            time.sleep(delay)

            # apply delay multiplier to delay
            delay *= delay_mult

            # decrement remaining tries
            retries -= 1


def get_fixed_usage(config: Config):
    usage = {}
    for metric, data in config.usage_metrics.items():
        usage[metric] = data.get('minimum_consumption', 0)

    usage['reporting_time'] = date_to_string(get_now())
    return usage
