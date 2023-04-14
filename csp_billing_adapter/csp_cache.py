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

import math

from collections import namedtuple, defaultdict

from csp_billing_adapter.config import Config
from csp_billing_adapter.utils import (
    get_now,
    date_to_string,
    get_next_bill_time
)

Usage = namedtuple('Usage', 'usage version timestamp')
namespace = 'neuvector-csp-billing-adapter'


def create_cache(hook, config: Config):
    now = get_now()
    next_bill_time = get_next_bill_time(now, config.billing_interval)

    cache = {
        'adapter_start_time': date_to_string(now),
        'next_bill_time': next_bill_time,
        'usage_records': [],
        'last_bill': {}
    }

    hook.save_cache(config=config, cache=cache)


def add_usage_record(hook, config: Config, record: Usage):
    cache = hook.get_cache(config=config)
    cache['usage_records'].append(dict(record._asdict()))
    hook.update_cache(config=config, cache=cache, replace=True)


def cache_meter_record(
    hook,
    config: Config,
    record_id: str,
    dimensions: dict,
    timestamp: str
):
    data = {
        'last_bill': {
            'dimensions': dimensions,
            'record_id': record_id,
            'timestamp': timestamp
        },
        'usage_records': []
    }

    hook.update_cache(config=config, cache=data)


def get_max_usage(usage_records: list, config: Config):
    max_usage = defaultdict(int)

    for record in usage_records:
        for dimension, units in record:
            if dimension == 'timestamp':
                continue

            if units > max_usage[dimension]:
                max_usage[dimension] = units

    return max_usage


def get_average_usage(usage_records: list):
    if not usage_records:
        return {}

    total_usage = defaultdict(int)
    for record in usage_records:
        for dimension, units in record:
            if dimension == 'timestamp':
                continue

            total_usage[dimension] += record.get(dimension, 0)

    average_usage = {}
    for dimension, usage in total_usage:
        average_usage[dimension] = math.ceil(usage / len(usage_records))


def get_billable_usage(
    usage_records: list,
    consumption_model: str
):
    if consumption_model == 'max':
        usage = get_max_usage(usage_records)
    elif consumption_model == 'average':
        usage = get_average_usage(usage_records)

    return usage


def get_bulk_dimensions(
    billable_usage: dict,
    dimensions: dict
):
    billed_dimensions = []

    for dimension_type, units in billable_usage:
        if dimension_type == 'timestamp':
            continue

        for dimension in dimensions[dimension_type]:
            if units < dimension['minimum']:
                continue
            if 'maximum' in dimension and units > dimension.get('maximum'):
                continue

            billed_usage = max(
                filter(None, [units, dimension.get('minimum_consumption')])
            )

            billed_dimensions.append({
                'dimension': dimension['dimension'],
                'units': billed_usage
            })

            return billed_dimensions


def get_billing_dimensions(config: Config, billable_usage: dict):
    if config.consumption_reporting == 'bulk':
        dimensions = get_bulk_dimensions(
            billable_usage,
            config.dimensions
        )
    elif config.consumption_reportin == 'tiered':
        pass

    return dimensions
