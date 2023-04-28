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

#
# Unit tests for the csp_billing_adapter.bill_utils
#

from unittest import mock

from pytest import (
    mark
)

from csp_billing_adapter.bill_utils import (
    get_average_usage,
    get_billable_usage,
    get_billing_dimensions,
    get_max_usage,
    get_volume_dimensions,
    process_metering
)
from csp_billing_adapter.csp_cache import (
    add_usage_record,
    create_cache
)
from csp_billing_adapter.csp_config import create_csp_config
from csp_billing_adapter.utils import (
    date_to_string,
    get_now,
    get_date_delta
)

now = date_to_string(get_now())
nowplus1hr = date_to_string(get_date_delta(get_now(), 3600))


def test_get_average_usage():
    metric1 = "dim1"
    usage_records1 = [
        {metric1: 1, 'reporting_time': now},
        {metric1: 1, 'reporting_time': now},
        {metric1: 1, 'reporting_time': now},
    ]
    metric2 = "dim2"
    usage_records2 = [
        {metric2: 1, 'reporting_time': now},
        {metric2: 2, 'reporting_time': now},
        {metric2: 3, 'reporting_time': now},
        {metric2: 4, 'reporting_time': nowplus1hr},
    ]

    average_usage = get_average_usage(metric1, [], now)
    assert average_usage == 0

    average_usage = get_average_usage(metric1, usage_records1, now)
    assert average_usage == 1

    average_usage = get_average_usage(metric2, usage_records2, now)
    assert average_usage == 2


def test_get_max_usage():
    metric1 = "dim1"
    usage_records1 = [
        {metric1: 1, 'reporting_time': now},
        {metric1: 1, 'reporting_time': now},
        {metric1: 1, 'reporting_time': now},
    ]
    metric2 = "dim2"
    usage_records2 = [
        {metric2: 1, 'reporting_time': now},
        {metric2: 2, 'reporting_time': now},
        {metric2: 3, 'reporting_time': now},
        {metric2: 4, 'reporting_time': nowplus1hr},
    ]

    max_usage = get_max_usage(metric1, [], now)
    assert max_usage == 0

    max_usage = get_max_usage(metric1, usage_records1, now)
    assert max_usage == 1

    max_usage = get_max_usage(metric2, usage_records2, now)
    assert max_usage == 3


def test_get_billage_usage_empty(cba_config):
    metric = "managed_node_count"

    billable_usage = get_billable_usage(
        usage_records=[],
        config=cba_config,
        empty_usage=True,
        bill_time=now
    )

    assert metric in billable_usage
    assert billable_usage[metric] == 0


def test_get_billable_usage_average(cba_config):
    metric = "managed_node_count"
    usage_records1 = [
        {metric: 1, 'reporting_time': now},
        {metric: 1, 'reporting_time': now},
        {metric: 1, 'reporting_time': now},
    ]
    usage_records2 = [
        {metric: 1, 'reporting_time': now},
        {metric: 2, 'reporting_time': now},
        {metric: 3, 'reporting_time': now},
        {metric: 4, 'reporting_time': nowplus1hr},
    ]

    billable_usage = get_billable_usage(
        usage_records=usage_records1,
        config=cba_config,
        empty_usage=False,
        bill_time=now
    )

    assert metric in billable_usage
    assert billable_usage[metric] == 1

    billable_usage = get_billable_usage(
        usage_records=usage_records2,
        config=cba_config,
        empty_usage=False,
        bill_time=now
    )

    assert metric in billable_usage
    assert billable_usage[metric] == 2


@mark.config('config_good_maximum.yaml')
def test_get_billable_usage_maximum(cba_config):
    config = cba_config
    metric = "managed_node_count"
    usage_records1 = [
        {metric: 1, 'reporting_time': now},
        {metric: 1, 'reporting_time': now},
        {metric: 1, 'reporting_time': now},
    ]
    usage_records2 = [
        {metric: 1, 'reporting_time': now},
        {metric: 2, 'reporting_time': now},
        {metric: 3, 'reporting_time': now},
        {metric: 4, 'reporting_time': nowplus1hr},
    ]

    billable_usage = get_billable_usage(
        usage_records=usage_records1,
        config=config,
        empty_usage=False,
        bill_time=now
    )

    assert metric in billable_usage
    assert billable_usage[metric] == 1

    billable_usage = get_billable_usage(
        usage_records=usage_records2,
        config=config,
        empty_usage=False,
        bill_time=now
    )

    assert metric in billable_usage
    assert billable_usage[metric] == 3


@mark.config('config_testing_mixed.yaml')
def test_get_volume_dimensions(cba_config):
    test_billable_usage = {
        "jobs": 72,
        "nodes": 7
    }
    test_tiers = {
        "jobs": "jobs_tier_3",
        "nodes": "nodes_tier_2"
    }

    for metric, usage in test_billable_usage.items():
        metric_dimensions = cba_config.usage_metrics[metric]['dimensions']
        billed_dimensions = {}

        get_volume_dimensions(
            usage_metric=metric,
            usage=usage,
            metric_dimensions=metric_dimensions,
            billed_dimensions=billed_dimensions
        )

        assert test_tiers[metric] in billed_dimensions
        assert billed_dimensions[test_tiers[metric]] == usage


@mark.config('config_testing_mixed.yaml')
def test_get_billing_dimensions(cba_config):
    test_billable_usage = {
        "jobs": 72,
        "nodes": 7
    }
    test_tiers = {
        "jobs": "jobs_tier_3",
        "nodes": "nodes_tier_2"
    }
    test_billed_dimensions = {
        test_tiers["jobs"]: test_billable_usage["jobs"],
        test_tiers["nodes"]: test_billable_usage["nodes"]
    }

    billed_dimensions = get_billing_dimensions(
        config=cba_config,
        billable_usage=test_billable_usage
    )

    assert billed_dimensions == test_billed_dimensions


@mark.config('config_testing_mixed.yaml')
def test_process_metering(cba_pm, cba_config):
    now = get_now()

    test_usage_data = [
        {
            "reporting_time": date_to_string(
                get_date_delta(now,
                               -(cba_config.reporting_interval * 2))),
            "jobs": 15,
            "nodes": 4
        },
        {
            "reporting_time": date_to_string(
                get_date_delta(now,
                               -(cba_config.reporting_interval * 1))),
            "jobs": 23,
            "nodes": 6
        },
        {
            "reporting_time": date_to_string(now),
            "jobs": 28,
            "nodes": 7
        },
        {
            "reporting_time": date_to_string(
                get_date_delta(
                    now,
                    (cba_config.reporting_interval * 1)
                )
            ),
            "jobs": 17,
            "nodes": 8
        }
    ]

    test_cache = cba_pm.hook.get_cache(config=cba_config)
    assert test_cache == {}

    create_cache(
        hook=cba_pm.hook,
        config=cba_config
    )

    test_cache = cba_pm.hook.get_cache(config=cba_config)
    assert 'adapter_start_time' in test_cache
    assert 'next_bill_time' in test_cache
    assert 'next_reporting_time' in test_cache
    assert 'usage_records' in test_cache
    assert test_cache["usage_records"] == []
    assert 'last_bill' in test_cache
    assert test_cache["last_bill"] == {}

    for record in test_usage_data:
        add_usage_record(
            hook=cba_pm.hook,
            config=cba_config,
            record=record
        )

    test_cache = cba_pm.hook.get_cache(config=cba_config)
    assert test_cache["usage_records"] == test_usage_data

    test_csp_config = cba_pm.hook.get_csp_config(config=cba_config)
    assert test_csp_config == {}

    create_csp_config(cba_pm.hook, cba_config)

    test_csp_config = cba_pm.hook.get_csp_config(config=cba_config)
    assert 'billing_api_access_ok' in test_csp_config
    assert test_csp_config['billing_api_access_ok'] is True
    assert 'timestamp' in test_csp_config
    assert 'expire' in test_csp_config
    assert 'errors' in test_csp_config
    assert test_csp_config['errors'] == []

    with mock.patch(
        'csp_billing_adapter.local_csp.randrange',
        return_value=0  # meter_billing will succeed
    ):
        cache_data = cba_pm.hook.get_cache(config=cba_config)
        process_metering(
            config=cba_config,
            cache=cache_data,
            hook=cba_pm.hook,
            empty_metering=True
        )

        test_cache = cba_pm.hook.get_cache(config=cba_config)
        assert test_cache["usage_records"] == cache_data['usage_records']
        assert test_cache["last_bill"] == {}

        test_csp_config = cba_pm.hook.get_csp_config(config=cba_config)
        assert test_csp_config['billing_api_access_ok'] is True
        assert test_csp_config['errors'] == []

        cache_data = cba_pm.hook.get_cache(config=cba_config)
        process_metering(
            config=cba_config,
            cache=cache_data,
            hook=cba_pm.hook,
            empty_metering=False
        )

        test_cache = cba_pm.hook.get_cache(config=cba_config)
        assert test_cache["usage_records"] == [
            record for record in test_usage_data
            if record['reporting_time'] > date_to_string(now)
        ]
        assert test_cache["last_bill"] != {}

        test_csp_config = cba_pm.hook.get_csp_config(config=cba_config)
        assert test_csp_config['billing_api_access_ok'] is True
        assert test_csp_config['errors'] == []
        assert 'usage' in test_csp_config
        assert 'last_billed' in test_csp_config

    with mock.patch(
        'csp_billing_adapter.local_csp.randrange',
        return_value=4  # meter_billing will fail
    ):
        cache_data = cba_pm.hook.get_cache(config=cba_config)
        process_metering(
            config=cba_config,
            cache=cache_data,
            hook=cba_pm.hook,
            empty_metering=True
        )

        test_cache = cba_pm.hook.get_cache(config=cba_config)
        assert test_cache["usage_records"] == cache_data['usage_records']
        assert test_cache["last_bill"] == cache_data['last_bill']

        test_csp_config = cba_pm.hook.get_csp_config(config=cba_config)
        assert test_csp_config['billing_api_access_ok'] is False
        assert test_csp_config['errors'] != []
