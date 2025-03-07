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
from unittest import mock

from pytest import raises, mark

from csp_billing_adapter.csp_cache import (
    add_usage_record,
    cache_meter_record,
    create_cache,
    record_valid,
    update_billing_dates
)
from csp_billing_adapter.exceptions import (
    FailedToSaveCacheError
)


def test_create_cache(cba_pm, cba_config):
    # cache should initially be empty
    assert cba_pm.hook.get_cache(config=cba_config) == {}

    new_cache = create_cache(cba_pm.hook, cba_config)

    cache = cba_pm.hook.get_cache(config=cba_config)

    assert 'adapter_start_time' in cache
    assert 'next_bill_time' in cache
    assert 'next_reporting_time' in cache
    assert 'usage_records' in cache
    assert cache['usage_records'] == []
    assert 'last_bill' in cache
    assert cache['last_bill'] == {}

    assert new_cache == cache


@mark.config('config_good_fixed.yaml')
def test_create_cache_fixed_billing(cba_pm, cba_config):
    # cache should initially be empty
    assert cba_pm.hook.get_cache(config=cba_config) == {}

    new_cache = create_cache(cba_pm.hook, cba_config)

    cache = cba_pm.hook.get_cache(config=cba_config)

    assert 'remaining_billing_dates' in cache
    assert 'configured_billing_dates' in cache
    assert 'end_of_support' in cache
    assert cache['next_reporting_time'] is None
    assert cache['trial_remaining'] == 0
    assert new_cache == cache


def test_create_cache_bad_config(cba_pm, cba_config):
    # cache should initially be empty
    assert cba_pm.hook.get_cache(config=cba_config) == {}

    with raises(AttributeError):
        create_cache(cba_pm.hook, {})


@mock.patch('csp_billing_adapter.utils.time.sleep')
def test_create_cache_exception_handling(
    mock_sleep,
    cba_pm,
    cba_config,
    caplog
):
    # cache should initially be empty
    assert cba_pm.hook.get_cache(config=cba_config) == {}

    # simulate save_cache() hook raising an exception
    error = Exception("Simulated save_cache() hook Exception")
    with mock.patch.object(
        cba_pm.hook,
        'save_cache',
        side_effect=error
    ):
        with raises(FailedToSaveCacheError):
            create_cache(cba_pm.hook, cba_config)
        assert str(error) in caplog.text


def test_add_usage_record(cba_pm, cba_config):
    base_date = datetime.datetime.now(datetime.timezone.utc)
    test_time1 = base_date + datetime.timedelta(minutes=1)
    test_time2 = base_date + datetime.timedelta(minutes=2)
    test_time3 = base_date - datetime.timedelta(days=5)

    test_usage1 = {
        'managed_node_count': 1,
        'reporting_time': test_time1.isoformat()
    }
    test_usage2 = {
        'managed_node_count': 3,
        'reporting_time': test_time2.isoformat()
    }
    test_usage3 = {
        'managed_node_count': 3,
        'reporting_time': test_time3.isoformat()
    }

    # cache should initially be empty
    assert cba_pm.hook.get_cache(config=cba_config) == {}

    create_cache(cba_pm.hook, cba_config)

    cache = cba_pm.hook.get_cache(config=cba_config)

    assert 'usage_records' in cache
    assert cache['usage_records'] == []

    # add first usage record
    add_usage_record(
        record=test_usage1,
        cache=cache,
        billing_interval=cba_config.billing_interval
    )

    assert cache['usage_records'] != []
    assert test_usage1 in cache['usage_records']
    assert cache['usage_records'] == [test_usage1]

    # add second usage record
    add_usage_record(
        record=test_usage2,
        cache=cache,
        billing_interval=cba_config.billing_interval
    )

    assert cache['usage_records'] != []
    assert test_usage2 in cache['usage_records']
    assert cache['usage_records'] == [test_usage1, test_usage2]

    # add second usage record again, verifying that it is not added
    add_usage_record(
        record=test_usage2,
        cache=cache,
        billing_interval=cba_config.billing_interval
    )

    assert cache['usage_records'] != []
    assert test_usage2 in cache['usage_records']
    assert cache['usage_records'] == [test_usage1, test_usage2]

    # add third usage record, verifying that it is not added
    add_usage_record(
        record=test_usage3,
        cache=cache,
        billing_interval=cba_config.billing_interval
    )

    assert cache['usage_records'] != []
    assert test_usage3 not in cache['usage_records']
    assert cache['usage_records'] == [test_usage1, test_usage2]


def test_cache_meter_record(cba_pm, cba_config):
    base_date = datetime.datetime.now(datetime.timezone.utc)
    test_time1 = base_date + datetime.timedelta(minutes=5)
    test_time2 = test_time1 + datetime.timedelta(minutes=5)
    test_time3 = test_time2 + datetime.timedelta(minutes=5)
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
    test_status = {
        'dim1': {
            'record_id': 'some_record_id',
            'status': 'submitted'
        },
        'dim2': {
            'record_id': 'some_record_id',
            'status': 'submitted'
        }
    }

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
            record=record,
            cache=cache,
            billing_interval=cba_config.billing_interval
        )

    assert cache['usage_records'] == test_usage_data

    # update cache to reflect successfully metered billing of first
    # usage record
    cache_meter_record(
        cache=cache,
        billing_status=test_status,
        dimensions=test_dimensions,
        metering_time=test_time1
    )

    assert cache['last_bill'] != {}
    assert 'billing_status' in cache['last_bill']
    assert cache['last_bill']['billing_status'] == test_status
    assert 'dimensions' in cache['last_bill']
    assert cache['last_bill']['dimensions'] == test_dimensions
    assert 'metering_time' in cache['last_bill']
    assert cache['last_bill']['metering_time'] == test_time1


def test_validate_usage_record(cba_pm, cba_config):
    base_date = datetime.datetime.now(datetime.timezone.utc)
    test_time1 = base_date + datetime.timedelta(minutes=1)
    test_time2 = base_date + datetime.timedelta(days=60)
    test_time3 = base_date - datetime.timedelta(days=60)

    create_cache(cba_pm.hook, cba_config)
    cache = cba_pm.hook.get_cache(config=cba_config)

    valid = record_valid(
        test_time1.isoformat(),
        cache['next_bill_time'],
        cba_config.billing_interval
    )
    assert valid

    valid = record_valid(
        test_time2.isoformat(),
        cache['next_bill_time'],
        cba_config.billing_interval
    )
    assert valid

    valid = record_valid(
        test_time3.isoformat(),
        cache['next_bill_time'],
        cba_config.billing_interval
    )
    assert not valid


@mark.config('config_good_fixed.yaml')
def test_update_billing_dates(cba_pm, cba_config):
    create_cache(cba_pm.hook, cba_config)
    cache = cba_pm.hook.get_cache(config=cba_config)

    cache['configured_billing_dates'] = '20200101,20210101,20220101'
    cache['end_of_support'] = '20230101'
    cache['next_bill_time'] = None

    update_billing_dates(cba_pm.hook, cache, cba_config)
    assert cache['configured_billing_dates'] == '20270101,20280101,20290101'
    assert cache['end_of_support'] == '2030-01-01T00:00:00+00:00'
    assert cache['next_bill_time'] == '2027-01-01T00:00:00+00:00'
    assert cache['remaining_billing_dates'] == ['20280101', '20290101']
