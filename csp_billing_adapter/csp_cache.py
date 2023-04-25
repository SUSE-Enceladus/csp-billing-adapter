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

from csp_billing_adapter.config import Config
from csp_billing_adapter.utils import (
    get_now,
    date_to_string,
    get_next_bill_time,
    get_date_delta
)


def create_cache(hook, config: Config):
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

    hook.save_cache(config=config, cache=cache)


def add_usage_record(hook, config: Config, record: dict):
    cache = hook.get_cache(config=config)

    if not cache.get('usage_records', []):
        cache['usage_records'] = [record]
        hook.update_cache(config=config, cache=cache, replace=True)
    else:
        last_record_time = cache['usage_records'][-1]['reporting_time']

        # Only include new usage records
        if record['reporting_time'] != last_record_time:
            cache['usage_records'].append(record)
            hook.update_cache(config=config, cache=cache, replace=True)


def cache_meter_record(
    hook,
    config: Config,
    record_id: str,
    dimensions: dict,
    metering_time: str,
    next_bill_time: str
):
    data = {
        'last_bill': {
            'dimensions': dimensions,
            'record_id': record_id,
            'metering_time': metering_time
        },
        'usage_records': [],
        'next_bill_time': next_bill_time
    }

    hook.update_cache(config=config, cache=data, replace=False)
