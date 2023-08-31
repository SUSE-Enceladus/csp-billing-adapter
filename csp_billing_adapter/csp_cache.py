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

"""
High-level (implementation agnostic) cache operations that leverage
Pluggy hooks to perform the implementation specific low-level cache
management operations.
"""

import functools
import logging

from csp_billing_adapter.config import Config
from csp_billing_adapter.exceptions import (
    FailedToSaveCacheError
)
from csp_billing_adapter.utils import (
    get_now,
    date_to_string,
    get_next_bill_time,
    get_date_delta,
    retry_on_exception,
    get_prev_bill_time,
    string_to_date
)

log = logging.getLogger('CSPBillingAdapter')


def create_cache(hook, config: Config) -> dict:
    """
    Initialise the cache data store based upon the settings specified
    for the CSP.

    :param hook:
        The Pluggy plugin manager hook used to call the save_cache()
        operation.
    :param config:
        The configuration settings associated with the CSP.
    """
    now = get_now()
    next_bill_time = get_next_bill_time(now, config.billing_interval)
    next_reporting_time = get_date_delta(now, config.reporting_interval)

    cache = {
        'adapter_start_time': date_to_string(now),
        'next_bill_time': date_to_string(next_bill_time),
        'next_reporting_time': date_to_string(next_reporting_time),
        'usage_records': [],
        'last_bill': {}
    }

    try:
        retry_on_exception(
            functools.partial(
                hook.save_cache,
                config=config,
                cache=cache
            ),
            logger=log,
            func_name="hook.save_cache"
        )
    except Exception as exc:
        log.error("Unable to save cache: %s", str(exc))
        # raise an application specific exception that will be
        # caught by the event loop in main() and cause an exit
        # with a failure status.
        raise FailedToSaveCacheError(str(exc)) from exc

    log.info("Initialized cache with: %s", cache)
    return cache


def record_valid(
    reporting_time: str,
    next_bill_time: str,
    billing_interval: str
):
    """
    Return True if the record reporting time is after the range start

    This prevents any record that is older than the current billing
    period from ending up in cache.

    :param reporting_time:
        The time the record was reported from product.
    :param next_bill_time:
        The end of the current billing period.
    :param billing_interval:
        The cadence for metering billing.
    """
    range_end = string_to_date(next_bill_time)
    range_start = get_prev_bill_time(
        range_end,
        billing_interval
    )
    return range_start <= string_to_date(reporting_time)


def add_usage_record(
    record: dict,
    cache: dict,
    billing_interval: str
) -> None:
    """
    Add a new 'record' to the cache data store's usage_records list,
    avoiding duplicate records by ensuring that the new record's
    reporting time doesn't match that of the last record saved.

    :param record:
        The record to add to the cache.
    :param cache:
        Cache to add the record to.
    :param billing_interval:
        The cadence for meter billing.
    """
    valid = record_valid(
        record['reporting_time'],
        cache['next_bill_time'],
        billing_interval
    )
    if not valid:
        log.info('Skipping invalid usage record: %s', record)
        return

    if not cache.get('usage_records', []):
        log.info('Initial usage record: %s', record)
        cache['usage_records'] = [record]
    else:
        last_record_time = cache['usage_records'][-1]['reporting_time']

        # Only include new usage records
        if record['reporting_time'] != last_record_time:
            log.info('Appending usage record: %s', record)
            cache['usage_records'].append(record)
        else:
            log.info('Skipping duplicate usage record: %s', record)


def cache_meter_record(
    cache: dict,
    billing_status: dict,
    dimensions: dict,
    metering_time: str
) -> None:
    """
    Update the cache data store to reflect the fact that a successful CSP
    metering operation was performed, storing the status returned by
    the CSP, the billing dimensions submitted in the metering operation,
    the time at which it was performed, and the time after which the next
    billing operation will be performed.

    :param billing_status:
        A mapping of dimensions to status. This includes record ids
        returned by the CSP to track the billing submission, status,
        and any error messages.
    :param dimensions: The billing dimensions submitted to the CSP.
    :param metering_time: The time at which the submission occurred.
    """
    cache['last_bill'] = {
        'dimensions': dimensions,
        'billing_status': billing_status,
        'metering_time': metering_time
    }
