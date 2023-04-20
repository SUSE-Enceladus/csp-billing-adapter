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
# Unit tests for the csp_billing_adapter.csp_cache when called via hooks
#

from csp_billing_adapter.csp_cache import (
    add_usage_record,
    cache_meter_record,
    create_cache,
    get_average_usage,
    get_billable_usage,
    get_max_usage,
    get_volume_dimensions
)

from pytest import raises


def test_create_cache(cba_pm, cba_config):
    # cache should initially be empty
    assert cba_pm.hook.get_cache(config=cba_config) == {}

    print(f'config: {cba_config!r}')

    create_cache(cba_pm.hook, cba_config)

    cache = cba_pm.hook.get_cache(config=cba_config)

    assert 'adapter_start_time' in cache
    assert 'next_bill_time' in cache
    assert 'usage_records' in cache
    assert cache['usage_records'] == []
    assert 'last_bill' in cache
    assert cache['last_bill'] == {}


def test_create_cache_bad_config(cba_pm, cba_config):
    # cache should initially be empty
    assert cba_pm.hook.get_cache(config=cba_config) == {}

    with raises(AttributeError):
        create_cache(cba_pm.hook, {})


def test_add_usage_record(cba_pm, cba_config):
    test_usage1 = dict(a=1, b=2)
    test_usage2 = dict(c=3, d=4)

    # cache should initially be empty
    assert cba_pm.hook.get_cache(config=cba_config) == {}

    create_cache(cba_pm.hook, cba_config)

    cache = cba_pm.hook.get_cache(config=cba_config)

    assert 'usage_records' in cache
    assert cache['usage_records'] == []

    add_usage_record(
        cba_pm.hook,
        config=cba_config,
        record=test_usage1
    )

    cache = cba_pm.hook.get_cache(config=cba_config)

    assert cache['usage_records'] != []
    assert test_usage1 in cache['usage_records']
    assert cache['usage_records'] == [test_usage1]

    add_usage_record(
        cba_pm.hook,
        config=cba_config,
        record=test_usage2
    )

    cache = cba_pm.hook.get_cache(config=cba_config)

    assert cache['usage_records'] != []
    assert test_usage2 in cache['usage_records']
    assert cache['usage_records'] == [test_usage1, test_usage2]


def test_cache_meter_record(cba_pm, cba_config):
    test_usage = dict(a=1, b=2)
    test_dimensions = dict(c=3, d=4)
    test_record_id = "some_record_id"
    test_timestamp = "some_time"

    # cache should initially be empty
    assert cba_pm.hook.get_cache(config=cba_config) == {}

    create_cache(cba_pm.hook, cba_config)

    cache = cba_pm.hook.get_cache(config=cba_config)

    assert 'usage_records' in cache
    assert cache['usage_records'] == []
    assert 'last_bill' in cache
    assert cache['last_bill'] == {}

    add_usage_record(
        cba_pm.hook,
        config=cba_config,
        record=test_usage
    )

    cache = cba_pm.hook.get_cache(config=cba_config)

    assert cache['usage_records'] != []
    assert test_usage in cache['usage_records']
    assert cache['usage_records'] == [test_usage]
    assert 'last_bill' in cache
    assert cache['last_bill'] == {}

    cache_meter_record(
        cba_pm.hook,
        config=cba_config,
        record_id=test_record_id,
        dimensions=test_dimensions,
        timestamp=test_timestamp
    )

    cache = cba_pm.hook.get_cache(config=cba_config)

    assert cache['usage_records'] == []
    assert cache['last_bill'] != {}
    assert 'record_id' in cache['last_bill']
    assert cache['last_bill']['record_id'] == test_record_id
    assert 'dimensions' in cache['last_bill']
    assert cache['last_bill']['dimensions'] == test_dimensions
    assert 'timestamp' in cache['last_bill']
    assert cache['last_bill']['timestamp'] == test_timestamp
    assert cache['usage_records'] == []


# NOTE: This test will need to be re-worked once the final implementation
# of usage record management.
def test_get_average_usage(cba_config):
    usage_records = [
        {"timestamp": "time1", "dim1": 1, "dim2": 1},
        {"timestamp": "time2", "dim1": 1, "dim2": 2},
        {"timestamp": "time3", "dim1": 1, "dim2": 3},
    ]

    average_usage = get_average_usage(usage_records)

    assert average_usage['dim1'] == 1
    assert average_usage['dim2'] == 2


# NOTE: This test will need to be re-worked once the final implementation
# of usage record management.
def test_get_max_usage(cba_config):
    usage_records = [
        {"timestamp": "time1", "dim1": 1, "dim2": 1},
        {"timestamp": "time2", "dim1": 1, "dim2": 2},
        {"timestamp": "time3", "dim1": 1, "dim2": 3},
    ]

    max_usage = get_max_usage(usage_records, cba_config)

    assert max_usage['dim1'] == 1
    assert max_usage['dim2'] == 3


# NOTE: This test will need to be re-worked once the final implementation
# of usage record management.
def test_get_billage_usage_average(cba_config):
    usage_records = [
        {"timestamp": "time1", "dim1": 1, "dim2": 1},
        {"timestamp": "time2", "dim1": 1, "dim2": 2},
        {"timestamp": "time3", "dim1": 1, "dim2": 3},
    ]

    average_usage = get_billable_usage(usage_records, 'average', cba_config)

    assert average_usage['dim1'] == 1
    assert average_usage['dim2'] == 2


# NOTE: This test will need to be re-worked once the final implementation
# of usage record management.
def test_get_billage_usage_max(cba_config):
    usage_records = [
        {"timestamp": "time1", "dim1": 1, "dim2": 1},
        {"timestamp": "time2", "dim1": 1, "dim2": 2},
        {"timestamp": "time3", "dim1": 1, "dim2": 3},
    ]

    average_usage = get_billable_usage(usage_records, 'max', cba_config)

    assert average_usage['dim1'] == 1
    assert average_usage['dim2'] == 3


# NOTE: This test will need to be re-worked once the final implementation
# of usage record management.
def test_get_volume_dimensions():
    test_billable_usage = {
        "timestamp": "some_timestamp",
        "dim1": 1,
        "dim2": 100,
    }
    test_dimensions = {
        "dim1": [
            {
                "dimension": "dim1_bin1",
                "minimum_consumption": 5,
                "minimum": 0,
                "maximum": 20
            },
            {
                "dimension": "dim1_bin2",
                "minimum": 20,
                "maximum": 50
            },
            {
                "dimension": "dim1_bin3",
                "minimum": 50,
            }
        ],
        "dim2": [
            {
                "dimension": "dim2_bin1",
                "minimum_consumption": 5,
                "minimum": 0,
                "maximum": 20
            },
            {
                "dimension": "dim2_bin2",
                "minimum": 20,
                "maximum": 50
            },
            {
                "dimension": "dim2_bin3",
                "minimum": 50
            }
        ]
    }

    volume_dimensions = get_volume_dimensions(
        test_billable_usage,
        test_dimensions
    )

    print(f'volume_dimensions = {volume_dimensions!r}')
    assert volume_dimensions[0] == dict(dimension="dim1_bin1", units=5)
    assert volume_dimensions[1] == dict(dimension="dim2_bin3", units=100)
