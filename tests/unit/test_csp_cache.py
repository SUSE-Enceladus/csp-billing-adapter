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
# Unit tests for the csp_billing_adapter.csp_cache
#

import datetime

from csp_billing_adapter.csp_cache import (
    add_usage_record,
    cache_meter_record,
    create_cache
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
    assert 'next_reporting_time' in cache
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
    test_time1 = datetime.datetime.now(datetime.timezone.utc)
    test_time2 = test_time1 + datetime.timedelta(seconds=5)
    test_usage1 = {
        'managed_node_count': 1,
        'reporting_time': test_time1.isoformat()
    }
    test_usage2 = {
        'managed_node_count': 3,
        'reporting_time': test_time2.isoformat()
    }

    # cache should initially be empty
    assert cba_pm.hook.get_cache(config=cba_config) == {}

    create_cache(cba_pm.hook, cba_config)

    cache = cba_pm.hook.get_cache(config=cba_config)

    assert 'usage_records' in cache
    assert cache['usage_records'] == []

    # add first usage record
    add_usage_record(
        cba_pm.hook,
        config=cba_config,
        record=test_usage1
    )

    cache = cba_pm.hook.get_cache(config=cba_config)

    assert cache['usage_records'] != []
    assert test_usage1 in cache['usage_records']
    assert cache['usage_records'] == [test_usage1]

    # add second usage record
    add_usage_record(
        cba_pm.hook,
        config=cba_config,
        record=test_usage2
    )

    cache = cba_pm.hook.get_cache(config=cba_config)

    assert cache['usage_records'] != []
    assert test_usage2 in cache['usage_records']
    assert cache['usage_records'] == [test_usage1, test_usage2]

    # add second usage record again, verifying that it is not added
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
    test_time1 = datetime.datetime.now(datetime.timezone.utc)
    test_time2 = test_time1 + datetime.timedelta(seconds=5)
    test_time3 = test_time2 + datetime.timedelta(seconds=5)
    test_usage_data = [
        {
            'managed_node_count': 1,
            'reporting_time': test_time1.isoformat()
        },
        {
            'managed_node_count': 1,
            'reporting_time': test_time3.isoformat()
        }
    ]
    test_dimensions = {'dim1': 1, 'dim2': 2}
    test_record_id = "some_record_id"

    # cache should initially be empty
    assert cba_pm.hook.get_cache(config=cba_config) == {}

    # initialise the cache
    create_cache(cba_pm.hook, cba_config)

    # verify cache contents correspond to an initialised cache
    cache = cba_pm.hook.get_cache(config=cba_config)

    assert 'usage_records' in cache
    assert cache['usage_records'] == []
    assert 'last_bill' in cache
    assert cache['last_bill'] == {}
    assert 'next_bill_time' in cache

    # add usage records from test_usage_data
    for record in test_usage_data:
        add_usage_record(
            cba_pm.hook,
            config=cba_config,
            record=record
        )

    # verify cache now has expected usage records
    cache = cba_pm.hook.get_cache(config=cba_config)

    assert cache['usage_records'] == test_usage_data

    # update cache to reflect successfully metered billing of first
    # usage record
    cache_meter_record(
        cba_pm.hook,
        config=cba_config,
        record_id=test_record_id,
        dimensions=test_dimensions,
        metering_time=test_time1,
        next_bill_time=test_time2,
        remaining_records=[test_usage_data[1]]  # remove first record
    )

    # verify that usage_records has been updated correctly
    # and that last_bill has been updated appropriately
    cache = cba_pm.hook.get_cache(config=cba_config)

    assert cache['usage_records'] == [test_usage_data[1]]
    assert cache['last_bill'] != {}
    assert 'record_id' in cache['last_bill']
    assert cache['last_bill']['record_id'] == test_record_id
    assert 'dimensions' in cache['last_bill']
    assert cache['last_bill']['dimensions'] == test_dimensions
    assert 'metering_time' in cache['last_bill']
    assert cache['last_bill']['metering_time'] == test_time1
    assert 'next_bill_time' in cache
    assert cache['next_bill_time'] == test_time2
