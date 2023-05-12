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
Utility functions for calculating CSP billing details for the usage
metrics specified in the provided config.
"""

import logging
import math

from csp_billing_adapter.csp_cache import cache_meter_record
from csp_billing_adapter.exceptions import (
    NoMatchingVolumeDimensionError
)
from csp_billing_adapter.utils import (
    date_to_string,
    get_next_bill_time,
    get_prev_bill_time,
    get_now,
    get_date_delta,
    string_to_date
)
from csp_billing_adapter.config import Config

log = logging.getLogger('CSPBillingAdapter')


def get_max_usage(metric: str, usage_records: list) -> int:
    """
    Determines the maximum usage value of the given 'metric' in the
    provided 'usage_records' list, defaulting to 0 if not found.

    :param metric: The metric to search for in the usage_records.
    :param usage_records: The list of usage records to process.
    :return:
        The maximum value found for the specified metric or 0 if
        no matching usage_records were found.
    """
    # In case of no records usage is 0
    # This prevents value error when calling max
    if not usage_records:
        log.debug("No usage records, returning 0")
        return 0

    max_usage = max(record.get(metric, 0) for record in usage_records)

    log.info(
        "Metric: %s, max: %d, records: %s",
        repr(metric),
        max_usage,
        usage_records
    )
    return max_usage


def get_average_usage(metric: str, usage_records: list) -> int:
    """
    Determines the average usage value of the given 'metric' in the
    provided 'usage_records' list, defaulting to 0 if not found.

    :param metric: The metric to search for in the usage_records.
    :param usage_records: The list of usage records to process.
    :return:
        The average of the values found for the specified metric or
        0 if no matching usage_records were found.
    """
    # In case of no records usage is 0
    # This prevents divide by zero to get average
    if not usage_records:
        log.debug("No usage records, returning 0")
        return 0

    total_usage = sum(record.get(metric, 0) for record in usage_records)
    average_usage = math.ceil(total_usage / len(usage_records))

    log.info(
        "Metric: %s, average = %d, records: %s",
        repr(metric),
        average_usage,
        usage_records
    )
    return average_usage


def get_billable_usage(
    usage_records: list,
    config: Config,
    empty_usage: bool = False
) -> dict:
    """
    Processes the provided 'usage_records' to determine the billable
    usage details for the metrics specified in the 'config', using
    the aggregation method defined for the metric in the config, and
    returns a hash containing the determined usage details for each
    specified metric.

    If 'empty_usage' is specified as True, the returned hash mapping
    will specify a value of 0 for all usage metrics defined in the
    'config', which represents a zero value billable usage for those
    cases where we will be submitting metering more frequently, e.g.
    hourly, to a CSP than we want to submit actual billable usage,
    which may be on a monthly cadence.

    :param usage_records:
        The list of usage records to process, which has already been
        filtered to contain entries within the current billing period.
    :param config:
        The configuration specifying the metrics that need to be
        processed in the usage records list.
    :param empty_usage:
        Flag indicating whether to return a billable usage hash
        with all metrics reporting zero usage, rather than the
        actual billable usage. Defaults to False.
    :return:
        Returns a hash mapping metric names to calculated usage,
        factoring in specified minimum chargeable usage for each
        metric, if it is specified in the config.
    """
    billable_usage = {}

    if empty_usage:
        log.debug("Return 0 for all metrics, empty_usage set")
        return {metric: 0 for metric in config.usage_metrics}

    for metric, data in config.usage_metrics.items():
        if data['usage_aggregation'] == 'average':
            usage = get_average_usage(metric, usage_records)
        elif data['usage_aggregation'] == 'maximum':
            usage = get_max_usage(metric, usage_records)

        billable_usage[metric] = max(
            usage,
            data.get('minimum_consumption', 0)
        )

    log.info(
        "Billable usage: %s, records: %s",
        billable_usage,
        usage_records
    )
    return billable_usage


def get_volume_dimensions(
    usage_metric: str,
    usage: int,
    metric_dimensions: dict,
    billed_dimensions: dict
) -> None:
    """
    For the metric specified by 'usage_metric', with the given
    'usage' value, determine the appropiate volume dimension tier
    that corresponds to that usage level, in the 'metric_dimensions'
    hash, and update the 'billed_dimensions' hash with an entry
    mapping that tier's name to the specified usage amount.

    :param usage_metric: The metric being processed.
    :param usage: The calculated usage for the specified metric.
    :param metric_dimensions:
        The hash specifying the volume dimension tiers for the
        specified metric.
    :param billed_dimensions:
        The hash that will be updated with an entry mapping the
        determined volume dimension tier's name to the specified
        usage value.
    """
    for dimension in metric_dimensions:
        if 'min' in dimension and usage < dimension['min']:
            log.debug("Skipping as usage < min")
            continue

        if 'max' in dimension and usage > dimension['max']:
            log.debug("Skipping as usage < min")
            continue

        billed_dimensions[dimension['dimension']] = usage

        log.info(
            "Metric: %s=%d, Volume dimension: %s",
            usage_metric,
            usage,
            billed_dimensions[dimension['dimension']]
        )

        # All usage is billed in volume to the matching dimension
        break
    else:
        log.error(
            "Failed to find a matching dimension entry for %s=%d",
            usage_metric,
            usage
        )
        raise NoMatchingVolumeDimensionError(
            usage_metric,
            usage
        )


def get_billing_dimensions(
    config: Config,
    billable_usage: dict
) -> dict:
    """
    Construct a hash mapping each metric's appropriate billable
    dimension name to it's usage value in the 'billable_usage'
    hash, using the metric's dimension configuration settings
    from the provided 'config'.

    :param config:
        The configuration specifying the metrics that need to be
        processed in the usage records list.
    :param billable_usage:
        A hash mapping the usage metrics specific in the 'config' to
        their calculated usage values.
    :return:
        A hash mapping each metric tier's name to it's associated
        usage value.
    """
    billed_dimensions = {}

    log.debug(
        "Determining billable dimensions for usage: %s",
        billable_usage
    )

    for usage_metric, usage in billable_usage.items():
        metric_config = config.usage_metrics[usage_metric]
        consumption_reporting = metric_config['consumption_reporting']

        if consumption_reporting == 'volume':
            log.debug(
                "Determining volume dimensions for %s=%d",
                usage_metric,
                usage
            )
            get_volume_dimensions(
                usage_metric,
                usage,
                metric_config['dimensions'],
                billed_dimensions
            )
        else:
            # Stubbed for different consumption reporting models in future
            pass

    log.info(
        "Determined billable dimensions %s for usage %s",
        billed_dimensions,
        billable_usage
    )
    return billed_dimensions


def filter_usage_records_by_date_range(
    usage_records: list,
    range_start: str,
    range_end: str
) -> list:
    """
    Returns the list of 'usage_records' filtered to remove records
    that fall outside the date range, starting at 'range_start' up
    to, but not including, 'range_end'.

    :param usage_records: The list of usage records to be filtered.
    :param range_start: The inclusive start of the date range.
    :param range_end: The exclusive end of the date range.
    :return:
        The set of usage records that falls within the specified
        date range.
    """
    log.info(
        "Filtering records for %s <= reporting_time < %s",
        range_start,
        range_end
    )
    return [record for record in usage_records
            if range_start <= record['reporting_time'] < range_end]


def filter_usage_records_in_billing_period(
    usage_records: list,
    config: Config,
    billing_period_end: str
) -> list:
    """
    Returns the list of 'usage_records' filtered to remove records
    that fall outside the billing period ending at 'billing_period_end',
    using the billing period duration specified in 'config'.

    :param usage_records: The list of usage records to be filtered.
    :param config:
        The configuration specifying the metrics that need to be
        processed in the usage records list.
    :param billing_period_end:
        The end of the current billing period, which is used to
        determine the appropriate set of records to filter onG.
    :return:
        The set of usage records that falls within the billing period
        that ending at 'billing_period_end'.
    """
    # determine time range to filter records for
    range_end = string_to_date(billing_period_end)
    range_start = get_prev_bill_time(
        range_end,
        config.billing_interval
    )

    # retrieve the records that fall within the specified range
    filtered_records = filter_usage_records_by_date_range(
        usage_records,
        date_to_string(range_start),
        date_to_string(range_end)
    )

    log.debug("Filtered records: %s", filtered_records)

    return filtered_records


def process_metering(
    config: Config,
    cache: dict,
    hook,
    empty_metering: bool = False,
    dry_run: bool = False
) -> None:
    """
    Handle the CSP metering process, updating the csp_config and cache
    data stores appropriately.
    The metering process consists of a number of steps, starting with
    retrieving the lastest billable usage details, or zeroed usage
    details if 'empty_metering' is specified as True.
    Next the billing dimensions hash is determined for those billable
    usage details, which are used to perform a meter_billing() operation
    against the CSP, via the registered Pluggy hook.
    If the meter_billing() operation fails, the csp_config data store will
    be updated to reflect that failure.
    Otherwise the csp_config data store will be updated to reflect that
    a metering operation was successfully performed at that time, with
    the validity expiration time updated to reflect the next metering
    time. Additionally, if 'empty_metering' is specified as False, the
    cache data store will be updated to reflect that a successful
    metering operation occurred, updating the metering time, the next
    bill time and saving the metering record id and submitted billing
    dimensions, and similarly the csp_config will be updated with the
    latest billable usage details and the and the time that the last
    bill was submitted..

    :param config:
        The configuration specifying the metrics that need to be
        processed to determine billable usage and dimensions.
    :param cache:
        The cache data store contents that will be used to determine
        the billable usage details.
    :param hook:
        The Pluggy plugin manager hook that will be used to call the
        meter_billing operation.
    :param empty_metering:
        A flag indicating if an empty (zeroed) metering record should be
        submitted, and if not not the csp_config and cache data stores
        will be updated appropriately to relfect a successful metering
        operation.
    :param dry_run:
        A flag that indicates if the metered billing will be performed
        as a dry run. If True the call to the CSP API is run as a test.
        No actual metering happens in this case. If False a bill will
        be metered based on usage and empty_metering flag.
    """
    now = get_now()
    log.debug(
        "Processing metering at time %s, empty_metering=%s",
        date_to_string(now),
        empty_metering
    )

    # select usage records appropriate for this billing period
    usage_records = cache.get('usage_records', [])
    billing_period_end = cache.get('next_bill_time')
    billable_records = filter_usage_records_in_billing_period(
        usage_records,
        config,
        billing_period_end
    )
    log.debug("Billable records: %s", billable_records)

    # the remaining records not selected as billable
    remaining_records = [record for record in usage_records
                         if record not in billable_records]
    log.debug("Remaining records: %s", remaining_records)

    # determine billable usage and associated billable dimensions
    billable_usage = get_billable_usage(
        billable_records,
        config,
        empty_usage=empty_metering
    )

    try:
        log.debug(
            "Attempting to billing processing for %s",
            billable_usage
        )

        billed_dimensions = get_billing_dimensions(
            config,
            billable_usage
        )

        log.debug(
            "Submitting billing for %s",
            billed_dimensions
        )

        record_id = hook.meter_billing(
            config=config,
            dimensions=billed_dimensions,
            timestamp=now,
            dry_run=dry_run
        )
    except Exception as e:
        log.exception(e)
        hook.update_csp_config(
            config=config,
            csp_config={
                'timestamp': date_to_string(now),
                'billing_api_access_ok': False,
                'errors': [str(e)]
            },
            replace=False
        )
    else:
        log.info(
            "Metering submitted, record_id: %s",
            record_id
        )

        metering_time = date_to_string(now)
        next_reporting_time = date_to_string(
            get_date_delta(now, config.reporting_interval)
        )

        cache_updates = {
            'next_reporting_time': next_reporting_time
        }

        csp_config_updates = {
            'billing_api_access_ok': True,
            'errors': [],
            'timestamp': metering_time,
            'expire': next_reporting_time
        }

        if not empty_metering:
            # Usage was billed
            next_bill_time = date_to_string(
                get_next_bill_time(
                    string_to_date(cache['next_bill_time']),
                    config.billing_interval
                )
            )
            log.debug(
                "Billable metering submitted, next bill time: %s",
                next_bill_time
            )

            cache_meter_record(
                hook,
                config,
                record_id,
                billed_dimensions,
                metering_time,
                next_bill_time,
                remaining_records=remaining_records
            )

            log.debug(
                "Adding metering details to csp_config updates: %s",
                csp_config_updates
            )
            csp_config_updates['usage'] = billable_usage
            csp_config_updates['last_billed'] = metering_time

        if not dry_run:
            log.info("Updating CSP config with: %s", csp_config_updates)
            hook.update_csp_config(
                config=config,
                csp_config=csp_config_updates,
                replace=False
            )

            log.info("Updating cache with: %s", cache_updates)
            hook.update_cache(
                config=config,
                cache=cache_updates,
                replace=False
            )
