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
    setup_logging,
    metering_test,
    update_logger_from_config
)
from csp_billing_adapter.exceptions import (
    CSPBillingAdapterException,
    NoMatchingVolumeDimensionError,
    FailedToSaveCSPConfigError
)
from csp_billing_adapter.utils import (
    get_now,
    get_date_delta,
    string_to_date,
    date_to_string
)


def test_adapter_version():
    """Verify the adapter version."""
    assert csp_billing_adapter.__version__ == "1.3.2"


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


def test_setup_logging():
    """Verify logging is being setup correctly."""
    log = setup_logging()
    assert log.name == "CSPBillingAdapter"


def test_update_logger_from_config():
    """Verify logging is updated correctly."""
    log = setup_logging()
    update_logger_from_config({'logging': {'level': 'WARN'}}, log)

    assert log.getEffectiveLevel() == 30

    log = setup_logging()
    expected_level = log.getEffectiveLevel()
    update_logger_from_config({}, log)

    assert log.getEffectiveLevel() == expected_level


def test_get_config(cba_pm, cba_config, cba_config_path, cba_log):
    """Verify correct operation of get_config()."""
    config = get_config(cba_config_path, cba_pm.hook, cba_log)

    assert config == cba_config


def test_initial_adapter_setup_no_errors(
    cba_pm,
    cba_config,
    cba_log,
    caplog
):
    """
    Verify that the initial_adapter_setup() works correctly using
    in-memory plugins.
    """
    setup_cache, setup_csp_config, initial_deploy = initial_adapter_setup(
        cba_pm.hook,
        cba_config,
        cba_log
    )

    assert initial_deploy
    assert setup_cache != {}
    assert setup_csp_config != {}

    cache = cba_pm.hook.get_cache(config=cba_config)
    assert cache == setup_cache

    csp_config = cba_pm.hook.get_csp_config(config=cba_config)
    assert csp_config == setup_csp_config

    setup_cache, setup_csp_config, initial_deploy = initial_adapter_setup(
        cba_pm.hook,
        cba_config,
        cba_log
    )
    assert not initial_deploy


@mock.patch('csp_billing_adapter.adapter.time.sleep')
def test_initial_adapter_setup_csp_config_errors(
    mock_sleep,
    cba_pm,
    cba_config,
    cba_log,
    caplog
):
    """
    Verify that the initial_adapter_setup() correctly handles
    exceptions from the csp_config management hook calls.
    """

    # test get_csp_config() hook raises an exception
    error = Exception('Simulated CSP Config Retrieval Error')
    with mock.patch.object(
        cba_pm.hook,
        'get_csp_config',
        side_effect=error
    ):
        # test save_csp_config() hook raises an exception
        with mock.patch.object(
            cba_pm.hook,
            'save_csp_config',
            side_effect=error
        ):
            with pytest.raises(FailedToSaveCSPConfigError):
                initial_adapter_setup(
                    cba_pm.hook,
                    cba_config,
                    cba_log
                )


@mock.patch('csp_billing_adapter.adapter.time.sleep')
def test_initial_adapter_setup_cache_errors(
    mock_sleep,
    cba_pm,
    cba_config,
    cba_log,
    caplog
):
    """
    Verify that the initial_adapter_setup() correctly handles
    exceptions from the cache management hook calls.
    """

    # test get_cache() hook raises an exception
    error = Exception('Simulated Cache Retrieval Error')
    with mock.patch.object(
        cba_pm.hook,
        'get_cache',
        side_effect=error
    ):
        cache, csp_config, initial_deploy = initial_adapter_setup(
            cba_pm.hook,
            cba_config,
            cba_log
        )
        assert str(error) in caplog.text


@mock.patch('csp_billing_adapter.local_csp.randrange')
@mock.patch('csp_billing_adapter.utils.time.sleep')
def test_event_loop_handler(
    mock_sleep,
    mock_randrange,
    cba_pm,
    cba_config,
    cba_log
):
    """Verify correct operation of event_loop_handler()."""
    # ensure meter_billing will succeed
    mock_randrange.return_value = 0

    # setup the adapter environment similar to what is done
    # inside the csp_billing_adapter.adapter.main()
    initial_adapter_setup(cba_pm.hook, cba_config, cba_log)

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

    event_loop_handler(
        cba_pm.hook,
        cba_config,
        cba_log,
        event_time,
        cache,
        csp_config
    )

    # This run should have added a new usage_record, but
    # not triggered any billing related updates to the cache.
    cache = cba_pm.hook.get_cache(config=cba_config)
    assert cache != {}
    assert cache['usage_records'] != []
    assert len(cache['usage_records']) == 1
    assert cache['last_bill'] == {}
    assert cache['trial_remaining'] == 1

    # Similarly the meter_billing() call should have succeeded
    # not triggered the generation of a new bill.
    csp_config = cba_pm.hook.get_csp_config(config=cba_config)
    assert csp_config != {}
    assert csp_config['billing_api_access_ok'] is True
    assert csp_config['errors'] == []
    assert 'usage' not in csp_config
    assert 'last_billed' not in csp_config
    assert csp_config['timestamp'] == date_to_string(event_time)
    assert csp_config['base_product'] == 'cpe:/o:suse:product:v1.2.3'

    #
    # Advance to next_reporting_time
    #

    # Simulate running the event loop at the next reporting_time,
    # which should just add a usage record entry, but not trigger
    # any billing updates.
    event_time = string_to_date(cache['next_reporting_time'])

    event_loop_handler(
        cba_pm.hook,
        cba_config,
        cba_log,
        event_time,
        cache,
        csp_config
    )

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
    assert csp_config['timestamp'] == date_to_string(event_time)

    #
    # Advance to next_bill_time
    #

    # Simulate the event loop running at the next billing time,
    # which should trigger billing related updates to the cache
    # and csp_config data stores
    event_time = string_to_date(cache['next_bill_time'])

    event_loop_handler(
        cba_pm.hook,
        cba_config,
        cba_log,
        event_time,
        cache,
        csp_config
    )

    # This run should in the usage_records list being cleared
    # in the case, along with the last_bill entry being updated
    # to reflect the billing event that was triggered.
    cache = cba_pm.hook.get_cache(config=cba_config)
    assert cache != {}
    assert cache['usage_records'] == []
    assert cache['last_bill'] != {}
    assert cache['trial_remaining'] == 0
    assert 'dimensions' in cache['last_bill']
    assert 'billing_status' in cache['last_bill']
    assert 'metering_time' in cache['last_bill']

    # The csp_config should now contain usage and last_billed
    # entries matching the triggered billing event
    csp_config = cba_pm.hook.get_csp_config(config=cba_config)
    assert csp_config != {}
    assert csp_config['billing_api_access_ok'] is True
    assert csp_config['errors'] == []
    assert 'usage' in csp_config
    assert 'last_billed' in csp_config
    assert csp_config['timestamp'] == date_to_string(event_time)

    #
    # Advance to next_reporting_time with a meter_billing() failure
    #

    # Ensure we get a failure for meter_billing
    mock_randrange.return_value = 4

    # Simulate a failed meter_billing operation, which should result
    # in an error being added to the errors list in the csp_config,
    # and the billing_api_access_ok flag being cleared.
    event_time = string_to_date(cache['next_reporting_time'])

    event_loop_handler(
        cba_pm.hook,
        cba_config,
        cba_log,
        event_time,
        cache,
        csp_config
    )

    # The last_bill entries should still be present.
    cache = cba_pm.hook.get_cache(config=cba_config)
    assert cache != {}
    assert cache['last_bill'] != {}
    assert 'dimensions' in cache['last_bill']
    assert 'billing_status' in cache['last_bill']
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
    assert csp_config['timestamp'] == date_to_string(event_time)


@mock.patch('csp_billing_adapter.utils.time.sleep')
def test_event_loop_handler_usage_data_error(
    mock_sleep,
    cba_pm,
    cba_config,
    cba_log,
    caplog
):
    event_time = get_now()

    error = Exception("Simulated failed get_usage_data() Error")
    with mock.patch.object(
        cba_pm.hook,
        'get_usage_data',
        side_effect=error
    ):
        initial_adapter_setup(cba_pm.hook, cba_config, cba_log)
        cache = cba_pm.hook.get_cache(config=cba_config)
        csp_config = cba_pm.hook.get_csp_config(config=cba_config)

        event_loop_handler(
            cba_pm.hook,
            cba_config,
            cba_log,
            event_time,
            cache,
            csp_config
        )

        # simulated error's message should be in the log
        assert str(error) in caplog.text

        # get_usage_data() succeeded message should not be in log
        assert 'Retrieved usage data: ' not in caplog.text

        # end of event loop processing message should be in log
        assert 'Finishing event loop processing' in caplog.text

        assert csp_config['timestamp'] == date_to_string(event_time)


@mock.patch('csp_billing_adapter.utils.time.sleep')
def test_event_loop_handler_update_cache_error(
    mock_sleep,
    cba_pm,
    cba_config,
    cba_log,
    caplog
):
    event_time = get_now()

    error = Exception("Simulated failed update_cache() Error")

    initial_adapter_setup(cba_pm.hook, cba_config, cba_log)
    cache = cba_pm.hook.get_cache(config=cba_config)
    csp_config = cba_pm.hook.get_csp_config(config=cba_config)

    with mock.patch.object(
        cba_pm.hook,
        'update_cache',
        side_effect=error
    ):
        event_loop_handler(
            cba_pm.hook,
            cba_config,
            cba_log,
            event_time,
            cache,
            csp_config
        )

        # simulated error's message should be in the log
        assert str(error) in caplog.text

        # update_cache exception handling's error message should be in log
        assert (
            'Failed to save cache to datastore: %s' % str(error)
        ) in caplog.text

        # confirm that csp_config's errors list contains expected error
        assert f'Cache failed to save: {error}' in csp_config['errors']

        # end of event loop processing message should be in log
        assert 'Finishing event loop processing' in caplog.text

        assert csp_config['timestamp'] == date_to_string(event_time)


@mock.patch('csp_billing_adapter.utils.time.sleep')
def test_event_loop_handler_update_csp_config_error(
    mock_sleep,
    cba_pm,
    cba_config,
    cba_log,
    caplog
):
    event_time = get_now()

    error = Exception("Simulated failed update_csp_config() Error")

    initial_adapter_setup(cba_pm.hook, cba_config, cba_log)
    cache = cba_pm.hook.get_cache(config=cba_config)
    csp_config = cba_pm.hook.get_csp_config(config=cba_config)

    with mock.patch.object(
        cba_pm.hook,
        'update_csp_config',
        side_effect=error
    ):
        event_loop_handler(
            cba_pm.hook,
            cba_config,
            cba_log,
            event_time,
            cache,
            csp_config
        )

        # simulated error's message should be in the log
        assert str(error) in caplog.text

        # update_csp_config exception handling's error message should be in log
        assert (
            'Failed to save csp_config to datastore: %s' % str(error)
        ) in caplog.text

        # confirm that csp_config's errors list contains expected error
        assert f'csp_config failed to save: {error}' in csp_config['errors']

        # end of event loop processing message should be in log
        assert 'Finishing event loop processing' in caplog.text

        assert csp_config['timestamp'] == date_to_string(event_time)


@mock.patch('csp_billing_adapter.local_csp.randrange')
@mock.patch('csp_billing_adapter.adapter.time.sleep')
@mock.patch('csp_billing_adapter.adapter.get_plugin_manager')
@mock.patch('csp_billing_adapter.adapter.get_config')
def test_main(
    mock_get_config,
    mock_get_pm,
    mock_sleep,
    mock_rand,
    cba_pm,
    cba_config
):

    mock_get_pm.return_value = cba_pm
    mock_get_config.return_value = cba_config
    mock_rand.return_value = 0

    # test catching Ctrl-C from time.sleep()
    mock_sleep.side_effect = KeyboardInterrupt('Mock Ctrl-C')

    with pytest.raises(SystemExit) as e:
        cba_main()
    assert e.value.code == 0

    mock_sleep.side_effect = None

    # test catching SystemExit
    with mock.patch(
        'csp_billing_adapter.adapter.event_loop_handler',
        side_effect=SystemExit(99)
    ):
        with pytest.raises(SystemExit) as e:
            cba_main()
        assert e.value.code == 99

    # test catching CSP Billing Adapter exception caused by
    # NoMatchingVolumeDimensionError.
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

    with mock.patch.object(
        cba_pm.hook,
        'meter_billing',
        side_effect=Exception('Mock Failure')
    ):
        with pytest.raises(SystemExit) as e:
            cba_main()
        assert e.value.code == 2


@pytest.mark.config('config_no_usage_metrics.yaml')
def test_metering_test_attrubute_error_handling(
    cba_pm,
    cba_config,
    cba_log,
    caplog
):
    err_msg = (
        "Billing adapter config is invalid. 'Config' object has no "
        "attribute 'usage_metrics'"
    )

    cache, csp_config, initial_deploy = initial_adapter_setup(
        cba_pm.hook,
        cba_config,
        cba_log
    )
    assert cache != {}
    assert csp_config != {}

    # test catching CSPBillingAdapterException caused by AttributeError
    with pytest.raises(CSPBillingAdapterException) as e:
        metering_test(
            cba_pm.hook,
            cba_config,
            cba_log,
            csp_config
        )
    assert err_msg in str(e)
    assert err_msg in caplog.text


@pytest.mark.config('config_no_dimensions.yaml')
def test_metering_test_key_error_handling(
    cba_pm,
    cba_config,
    cba_log,
    caplog
):
    err_msg = (
        "Billing adapter config is invalid. Config is missing "
        "'dimensions'"
    )

    cache, csp_config, initial_deploy = initial_adapter_setup(
        cba_pm.hook,
        cba_config,
        cba_log
    )
    assert cache != {}
    assert csp_config != {}

    # test catching CSPBillingAdapterException caused by KeyError
    with pytest.raises(CSPBillingAdapterException) as e:
        metering_test(
            cba_pm.hook,
            cba_config,
            cba_log,
            csp_config
        )
    assert err_msg in str(e)
    assert err_msg in caplog.text


@mock.patch('csp_billing_adapter.adapter.time.sleep')
def test_metering_test_meter_billing_failure(
    mock_sleep,
    cba_pm,
    cba_config,
    cba_log,
    caplog
):
    err_exc = Exception('Mock Failure')
    err_msg = (
        "Fatal error while validating metering API access: "
        f"{str(err_exc)}"
    )

    cache, csp_config, initial_deploy = initial_adapter_setup(
        cba_pm.hook,
        cba_config,
        cba_log
    )
    assert cache != {}
    assert csp_config != {}

    with mock.patch.object(
        cba_pm.hook,
        'meter_billing',
        side_effect=err_exc
    ):
        # test catching CSPBillingAdapterException caused by
        # meter_billing() fatal exception.
        with pytest.raises(CSPBillingAdapterException) as e:
            metering_test(
                cba_pm.hook,
                cba_config,
                cba_log,
                csp_config
            )
        assert err_msg in str(e)
        assert err_msg in caplog.text


@mock.patch('csp_billing_adapter.adapter.time.sleep')
def test_metering_test_meter_billing_and_update_csp_config_failure(
    mock_sleep,
    cba_pm,
    cba_config,
    cba_log,
    caplog
):
    err_exc = Exception('Mock Failure')
    err_msg1 = (
        "Fatal error while validating metering API access: "
        f"{str(err_exc)}"
    )
    err_msg2 = (
        "Failed to save csp_config to datastore: "
        f"{str(err_exc)}"
    )

    cache, csp_config, initial_deploy = initial_adapter_setup(
        cba_pm.hook,
        cba_config,
        cba_log
    )
    assert cache != {}
    assert csp_config != {}

    with mock.patch.object(
        cba_pm.hook,
        'meter_billing',
        side_effect=err_exc
    ):
        with mock.patch.object(
            cba_pm.hook,
            'update_csp_config',
            side_effect=err_exc
        ):
            # test catching CSPBillingAdapterException caused by
            # meter_billing() fatal exception along with an
            # update_csp_config() failure.
            with pytest.raises(CSPBillingAdapterException) as e:
                metering_test(
                    cba_pm.hook,
                    cba_config,
                    cba_log,
                    csp_config
                )
            assert err_msg1 in str(e)
            assert err_msg1 in caplog.text
            assert err_msg2 in caplog.text


@mock.patch('csp_billing_adapter.adapter.get_plugin_manager')
@mock.patch('csp_billing_adapter.adapter.setup_logging')
@mock.patch('csp_billing_adapter.adapter.get_config')
@mock.patch('csp_billing_adapter.adapter.event_loop_handler')
@mock.patch('csp_billing_adapter.adapter.get_now')
@mock.patch('csp_billing_adapter.adapter.time.sleep')
def test_main_sleep(
    mock_sleep,
    mock_get_now,
    mock_event_loop_handler,
    mock_get_config,
    mock_setup_logging,
    mock_get_pm,
    cba_pm,
    cba_config,
    cba_log,
    caplog
):
    now = get_now()
    processing_delay = 1.23

    # calculate the time when event loop "started"
    event_time = get_date_delta(
        now,
        -processing_delay
    )

    # this is the debug level message we expect to see in the log,
    # and debug level is enabled for the cba_log fixture
    expected_log_msg = (
        "Sleeping for %g seconds" % (
            cba_config.query_interval - (now - event_time).total_seconds()
        )
    )

    # set up our mock return values
    mock_get_pm.return_value = cba_pm
    mock_setup_logging.return_value = cba_log
    mock_get_config.return_value = cba_config
    mock_event_loop_handler.return_value = None

    # get_now() is called at the start of the main loop, and again to
    # get the current time to determine how much time to sleep for.
    mock_get_now.side_effect = [now, event_time, now]

    # time.sleep is called before the main loop runs, which needs to
    # succeed, but the next call, at the end of the main loop should
    # fail leading to SystemExit with exit status of 0.
    mock_sleep.side_effect = [
        None,
        KeyboardInterrupt('Mock Ctrl-C'),
    ]

    with mock.patch.object(
        cba_pm.hook,
        'meter_billing',
        return_value=None
    ):
        with pytest.raises(SystemExit) as e:
            cba_main()
        assert e.value.code == 0
        assert expected_log_msg in caplog.text


@pytest.mark.config('config_good_fixed.yaml')
@mock.patch('csp_billing_adapter.local_csp.randrange')
@mock.patch('csp_billing_adapter.utils.time.sleep')
def test_event_loop_handler_fixed_billing(
    mock_sleep,
    mock_randrange,
    cba_pm,
    cba_config,
    cba_log
):
    """Verify correct operation of event_loop_handler()."""
    # ensure meter_billing will succeed
    mock_randrange.return_value = 0

    # setup the adapter environment similar to what is done
    # inside the csp_billing_adapter.adapter.main()
    initial_adapter_setup(cba_pm.hook, cba_config, cba_log)

    # validate the initial state of the cache
    cache = cba_pm.hook.get_cache(config=cba_config)
    assert cache != {}
    assert cache['usage_records'] == []
    assert cache['last_bill'] == {}
    assert cache['remaining_billing_dates'] == ['20280101', '20290101']
    assert cache['configured_billing_dates'] == '20270101,20280101,20290101'
    assert cache['end_of_support'] == '2030-01-01T00:00:00+00:00'
    assert cache['next_reporting_time'] is None
    assert cache['trial_remaining'] == 0

    # validate the initial state of the csp_cache
    csp_config = cba_pm.hook.get_csp_config(config=cba_config)
    assert csp_config != {}
    assert csp_config['billing_api_access_ok'] is True
    assert 'timestamp' in csp_config
    assert csp_config['expire'] == '2030-01-01T00:00:00+00:00'
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

    event_loop_handler(
        cba_pm.hook,
        cba_config,
        cba_log,
        event_time,
        cache,
        csp_config
    )

    # This run should have added a new usage_record, but
    # not triggered any billing related updates to the cache.
    cache = cba_pm.hook.get_cache(config=cba_config)
    assert cache != {}
    assert cache['usage_records'] != []
    assert len(cache['usage_records']) == 1
    assert cache['last_bill'] == {}
    assert cache['trial_remaining'] == 0

    # Similarly the meter_billing() call should have succeeded
    # not triggered the generation of a new bill.
    csp_config = cba_pm.hook.get_csp_config(config=cba_config)
    assert csp_config != {}
    assert csp_config['billing_api_access_ok'] is True
    assert csp_config['errors'] == []
    assert 'usage' not in csp_config
    assert 'last_billed' not in csp_config
    assert csp_config['timestamp'] == date_to_string(event_time)
