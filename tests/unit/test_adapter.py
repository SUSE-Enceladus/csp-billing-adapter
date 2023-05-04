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

from unittest import mock

import pytest

import csp_billing_adapter
from csp_billing_adapter import (
    local_csp,
    memory_cache,
    memory_csp_config,
    product_api
)
from csp_billing_adapter.adapter import (
    event_loop_handler,
    get_config,
    get_plugin_manager,
    initial_adapter_setup,
    main as cba_main,
    setup_logging
)
from csp_billing_adapter.exceptions import (
    NoMatchingVolumeDimensionError
)
from csp_billing_adapter.utils import (
    get_now,
    string_to_date
)


def test_adapter_version():
    """Verify the adapter version."""
    assert csp_billing_adapter.__version__ == "0.0.1"


def test_get_plugin_manager(cba_config):
    """Verify that get_plugin_manager() works correctly."""
    pm = get_plugin_manager()

    # the testing plugins shouldn't be registered
    assert pm.is_registered(local_csp) is False
    assert pm.is_registered(memory_cache) is False
    assert pm.is_registered(memory_csp_config) is False
    assert pm.is_registered(product_api) is False

    # register the local_csp plugin so that we can call a
    # hook implementation that it provides
    pm.register(local_csp)

    assert pm.hook.get_csp_name(config=cba_config) == "local"


def test_setup_logging(cba_pm):
    """Verify logging is being setup correctly."""
    log = setup_logging(cba_pm.hook)

    assert log.name == "CSPBillingAdapter"


def test_get_config(cba_pm, cba_config, cba_config_path):
    """Verify correct operation of get_config()."""
    config = get_config(cba_config_path, cba_pm.hook)

    assert config == cba_config


def test_initial_adapter_setup(cba_pm, cba_config):
    """
    Verify that the initial_adapter_setup() works correctly using
    in-memory plugins.
    """
    initial_adapter_setup(cba_pm.hook, cba_config)

    cache = cba_pm.hook.get_cache(config=cba_config)
    assert cache != {}

    csp_config = cba_pm.hook.get_cache(config=cba_config)
    assert csp_config != {}


@mock.patch('csp_billing_adapter.local_csp.randrange')
def test_event_loop_handler(mock_randrange, cba_pm, cba_config):
    """Verify correct operation of event_loop_handler()."""
    # ensure meter_billing will succeed
    mock_randrange.return_value = 0

    # setup the adapter environment similar to what is done
    # inside the csp_billing_adapter.adapter.main()
    log = setup_logging(cba_pm.hook)
    assert log.name == ('CSPBillingAdapter')
    initial_adapter_setup(cba_pm.hook, cba_config)

    # validate the initial state of the cache
    cache = cba_pm.hook.get_cache(config=cba_config)
    assert cache != {}
    assert cache['usage_records'] == []
    assert cache['last_bill'] == {}

    # validate the initial state of the csp_cache
    csp_config = cba_pm.hook.get_csp_config(config=cba_config)
    assert csp_config != {}
    assert csp_config['billing_api_access_ok'] is True
    assert 'timestamp' in csp_config
    assert 'expire' in csp_config
    assert csp_config['errors'] == []
    assert 'usage' not in csp_config
    assert 'last_billed' not in csp_config

    #
    # Startup/first iteration
    #

    # Simulate running the first iteration of the event loop after
    # starting the csp-billing-adpater for the first time for a
    # given config.
    event_time = get_now()

    # Patch the get_now() call to return the current time
    # and simulate the first run of the event loop.
    with mock.patch('csp_billing_adapter.adapter.get_now',
                    return_value=event_time):
        loop_event_time = event_loop_handler(cba_pm.hook, cba_config)
        assert loop_event_time == event_time

        # This run should have added a new usage_record, but
        # not triggered any billing related updates to the cache.
        cache = cba_pm.hook.get_cache(config=cba_config)
        assert cache != {}
        assert cache['usage_records'] != []
        assert len(cache['usage_records']) == 1
        assert cache['last_bill'] == {}

        # Similarly the meter_billing() call should have succeeded
        # not triggered the generation of a new bill.
        csp_config = cba_pm.hook.get_csp_config(config=cba_config)
        assert csp_config != {}
        assert csp_config['billing_api_access_ok'] is True
        assert csp_config['errors'] == []
        assert 'usage' not in csp_config
        assert 'last_billed' not in csp_config

    #
    # Advance to next_reporting_time
    #

    # Simulate running the event loop at the next reporting_time,
    # which should just add a usage record entry, but not trigger
    # any billing updates.
    event_time = string_to_date(cache['next_reporting_time'])

    with mock.patch('csp_billing_adapter.adapter.get_now',
                    return_value=event_time):
        loop_event_time = event_loop_handler(cba_pm.hook, cba_config)
        assert loop_event_time == event_time

        # This run should have added another usage_record, but
        # not triggered any billing related updates to the cache.
        cache = cba_pm.hook.get_cache(config=cba_config)
        assert cache != {}
        assert cache['usage_records'] != []
        assert len(cache['usage_records']) == 2
        assert cache['last_bill'] == {}

        # Similarly the meter_billing() call should have succeeded
        # not triggered the generation of a new bill.
        csp_config = cba_pm.hook.get_csp_config(config=cba_config)
        assert csp_config != {}
        assert csp_config['billing_api_access_ok'] is True
        assert csp_config['errors'] == []
        assert 'usage' not in csp_config
        assert 'last_billed' not in csp_config

    #
    # Advance to next_bill_time
    #

    # Simulate the event loop running at the next billing time,
    # which should trigger billing related updates to the cache
    # and csp_config data stores
    event_time = string_to_date(cache['next_bill_time'])

    with mock.patch('csp_billing_adapter.adapter.get_now',
                    return_value=event_time):
        loop_event_time = event_loop_handler(cba_pm.hook, cba_config)
        assert loop_event_time == event_time

        # This run should in the usage_records list being cleared
        # in the case, along with the last_bill entry being updated
        # to reflect the billing event that was triggered.
        cache = cba_pm.hook.get_cache(config=cba_config)
        assert cache != {}
        assert cache['usage_records'] == []
        assert cache['last_bill'] != {}
        assert 'dimensions' in cache['last_bill']
        assert 'record_id' in cache['last_bill']
        assert 'metering_time' in cache['last_bill']

        # The csp_config should now contain usage and last_billed
        # entries matching the triggered billing event
        csp_config = cba_pm.hook.get_csp_config(config=cba_config)
        assert csp_config != {}
        assert csp_config['billing_api_access_ok'] is True
        assert csp_config['errors'] == []
        assert 'usage' in csp_config
        assert 'last_billed' in csp_config

    #
    # Advance to next_reporting_time with a meter_billing() failure
    #

    # Ensure we get a failure for meter_billing
    mock_randrange.return_value = 4

    # Simulate a failed meter_billing operation, which should result
    # in an error being added to the errors list in the csp_config,
    # and the billing_api_access_ok flag being cleared.
    event_time = string_to_date(cache['next_reporting_time'])

    with mock.patch('csp_billing_adapter.adapter.get_now',
                    return_value=event_time):
        loop_event_time = event_loop_handler(cba_pm.hook, cba_config)
        assert loop_event_time == event_time

        # A new usage record should have been added to the usage
        # records list in the cache, and the last_bill entries should
        # still be present.
        cache = cba_pm.hook.get_cache(config=cba_config)
        assert cache != {}
        assert cache['usage_records'] != []
        assert len(cache['usage_records']) == 1
        assert cache['last_bill'] != {}
        assert 'dimensions' in cache['last_bill']
        assert 'record_id' in cache['last_bill']
        assert 'metering_time' in cache['last_bill']

        # An error should have been added to the errors list in the
        # csp_config data store, and the billing_api_access_ok flag
        # should be cleared to reflect that an error occurred.
        csp_config = cba_pm.hook.get_csp_config(config=cba_config)
        assert csp_config != {}
        assert csp_config['billing_api_access_ok'] is False
        assert csp_config['errors'] != []
        assert 'usage' in csp_config
        assert 'last_billed' in csp_config


@mock.patch('csp_billing_adapter.adapter.get_plugin_manager')
@mock.patch('csp_billing_adapter.adapter.get_config')
def test_main(mock_get_config, mock_get_pm, cba_pm, cba_config):

    mock_get_pm.return_value = cba_pm
    mock_get_config.return_value = cba_config

    # test catching Ctrl-C
    with mock.patch(
        'csp_billing_adapter.adapter.event_loop_handler',
        side_effect=KeyboardInterrupt('Mock Ctrl-C')
    ):
        with pytest.raises(SystemExit) as e:
            cba_main()
        assert e.value.code == 0

    # test catching SystemExit
    with mock.patch(
        'csp_billing_adapter.adapter.event_loop_handler',
        side_effect=SystemExit(99)
    ):
        with pytest.raises(SystemExit) as e:
            cba_main()
        assert e.value.code == 99

    # test catching CSP Billing Adapter exception
    with mock.patch(
        'csp_billing_adapter.adapter.event_loop_handler',
        side_effect=NoMatchingVolumeDimensionError('metric', 9999)
    ):
        with pytest.raises(SystemExit) as e:
            cba_main()
        assert e.value.code == 2

    # test catching generic exception
    with mock.patch(
        'csp_billing_adapter.adapter.event_loop_handler',
        side_effect=Exception('Mock Failure')
    ):
        with pytest.raises(SystemExit) as e:
            cba_main()
        assert e.value.code == 1
