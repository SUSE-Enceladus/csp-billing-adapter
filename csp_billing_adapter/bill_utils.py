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

import math

from csp_billing_adapter.csp_cache import cache_meter_record
from csp_billing_adapter.utils import (
    date_to_string,
    get_next_bill_time,
    get_now,
    get_date_delta,
    string_to_date
)
from csp_billing_adapter.config import Config


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
        return 0

    max_usage = max(record.get(metric, 0) for record in usage_records)
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
        return 0

    total_usage = sum(record.get(metric, 0) for record in usage_records)
    average_usage = math.ceil(total_usage / len(usage_records))

    return average_usage


def get_billable_usage(
    usage_records: list,
    config: Config,
    empty_usage: False
) -> dict:
    """
    Processes the provided 'usage_records' to determine the billable
    usage details for the metrics specified in the 'config', using
    the aggregation method defined for the metric in the config, and
    returns a hash containing the determined usage details for each
    specified metric. The 'usage_records' list can be optionally
    cleared after processing, indicated by the 'empty_usage' flag.

    :param usage_records: The list of usage records to process.
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
            continue

        if 'max' in dimension and usage > dimension['max']:
            continue

        billed_dimensions[dimension['dimension']] = usage

        # All usage is billed in volume to the matching dimension
        break


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

    for usage_metric, usage in billable_usage.items():
        metric_config = config.usage_metrics[usage_metric]
        consumption_reporting = metric_config['consumption_reporting']

        if consumption_reporting == 'volume':
            get_volume_dimensions(
                usage_metric,
                usage,
                metric_config['dimensions'],
                billed_dimensions
            )
        else:
            # Stubbed for different consumption reporting models in future
            pass

    return billed_dimensions


def process_metering(
    config: Config,
    cache: dict,
    hook,
    empty_metering: bool = False
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
    time. Additionally, if 'empty_metering' was specified as True, the
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
    """
    now = get_now()

    billable_usage = get_billable_usage(
        cache.get('usage_records', []),
        config,
        empty_usage=empty_metering
    )
    billed_dimensions = get_billing_dimensions(
        config,
        billable_usage
    )

    try:
        record_id = hook.meter_billing(
            config=config,
            dimensions=billed_dimensions,
            timestamp=now
        )
    except Exception as e:
        hook.update_csp_config(
            config=config,
            csp_config={
                'billing_api_access_ok': False,
                'errors': [str(e)]
            },
            replace=False
        )
    else:
        metering_time = date_to_string(now)
        next_reporting_time = date_to_string(
            get_date_delta(now, config.reporting_interval)
        )

        data = {
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

            cache_meter_record(
                hook,
                config,
                record_id,
                billed_dimensions,
                metering_time,
                next_bill_time
            )

            data['usage'] = billable_usage
            data['last_billed'] = metering_time

        hook.update_csp_config(
            config=config,
            csp_config=data,
            replace=False
        )
        hook.update_cache(
            config=config,
            cache={'next_reporting_time': next_reporting_time},
            replace=False
        )
