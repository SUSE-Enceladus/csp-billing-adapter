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
test_utils is part of csp-billing-adapter and provides units tests
for the utils functions.
"""

import datetime
import functools
from unittest import mock

from pytest import raises

from csp_billing_adapter import utils


def test_good_date_to_string():
    """Test working utils.utils.date_to_string"""
    assert utils.date_to_string(datetime.datetime(2023, 4, 20, 13, 8, 30)) == \
        '2023-04-20T13:08:30'


def test_bad_date_to_string_attribute_error():
    """Text exception raised for utils.date_to_string"""
    with raises(AttributeError, match="foo"):
        utils.date_to_string("foo")


def test_bad_date_to_string_value_error():
    """Text exception raised for utils.date_to_string"""
    with raises(ValueError, match="month must be in"):
        utils.date_to_string(datetime.datetime(2023, 15, 20, 13, 8, 30))


def test_good_string_to_date():
    """Test working utils.string_to_date"""
    assert utils.string_to_date('2023-04-20T13:08:30') == \
        datetime.datetime(2023, 4, 20, 13, 8, 30)


def test_bad_string_to_date():
    """Text exception raised for utils.string_to_date"""
    with raises(ValueError, match='foo'):
        utils.string_to_date('foo')


def test_good_get_date_delta():
    """Test working utils.get_date_delta"""
    assert utils.get_date_delta(
        datetime.datetime(2023, 4, 20, 13, 8, 30),
        180) == \
        datetime.datetime(2023, 4, 20, 13, 11, 30)


def test_bad_get_date_delta_value_error():
    """Text exception raised for utils.get_date_delta"""
    with raises(ValueError, match="month must be in"):
        utils.get_date_delta(
            datetime.datetime(2023, 15, 20, 13, 8, 30), 180
        )


def test_bad_get_date_delta_type_error():
    """Text exception raised for utils.get_date_delta"""
    with raises(TypeError, match="foo"):
        utils.get_date_delta(
            datetime.datetime(2023, 4, 20, 13, 8, 30),
            'foo'
        )


def test_good_get_next_bill_time_hourly():
    """Test working utils.get_next_bill_time"""
    assert utils.get_next_bill_time(
        datetime.datetime(2023, 4, 20, 13, 8, 30),
        'hourly') == \
        datetime.datetime(2023, 4, 20, 14, 8, 30)


def test_good_get_next_bill_time_monthly():
    """Test working utils.get_next_bill_time"""
    assert utils.get_next_bill_time(
        datetime.datetime(2023, 4, 20, 13, 8, 30),
        'monthly') == \
        datetime.datetime(2023, 5, 20, 13, 8, 30)


def test_good_get_next_bill_time_test():
    """Test working utils.get_next_bill_time"""
    assert utils.get_next_bill_time(
        datetime.datetime(2023, 4, 20, 13, 8, 30),
        'test') == \
        datetime.datetime(2023, 4, 20, 13, 13, 30)


def test_good_get_prev_bill_time_hourly():
    """Test working utils.get_prev_bill_time"""
    assert utils.get_prev_bill_time(
        datetime.datetime(2023, 4, 20, 14, 8, 30),
        'hourly') == \
        datetime.datetime(2023, 4, 20, 13, 8, 30)


def test_good_get_prev_bill_time_monthly():
    """Test working utils.get_prev_bill_time"""
    assert utils.get_prev_bill_time(
        datetime.datetime(2023, 5, 20, 13, 8, 30),
        'monthly') == \
        datetime.datetime(2023, 4, 20, 13, 8, 30)


def test_good_get_prev_bill_time_test():
    """Test working utils.get_prev_bill_time"""
    assert utils.get_prev_bill_time(
        datetime.datetime(2023, 4, 20, 13, 13, 30),
        'test') == \
        datetime.datetime(2023, 4, 20, 13, 8, 30)


def succeeding_func(message):
    """Helper function that returns passed argument."""
    return message


def failing_func(message):
    """Helper function that raises Exception with passed argument."""
    raise Exception(message)


def test_retry_on_exception_success(cba_log, caplog):
    """Verify correct handling of a successful function call."""

    message = "Mock testing"

    succeeding_call = functools.partial(succeeding_func, message)

    # test succeeding_call
    result = utils.retry_on_exception(
        succeeding_call,
        logger=cba_log
    )

    # ensure expected value was returned
    assert result == message

    # verify that we saw an attempt to call the function
    assert (
        "Attempting to run '%s'" % succeeding_call.func.__name__
    ) in caplog.text


@mock.patch('csp_billing_adapter.utils.time.sleep')
def test_retry_on_exception_failure(mock_sleep, cba_log, caplog):
    """Verify correct handling of a failing function call."""

    error = "Mock testing exception"

    failing_call = functools.partial(failing_func, error)

    exceptions = Exception
    retry_count = 3
    retry_delay = 1
    delay_factor = 1

    # test failing_call
    with raises(Exception) as exc:
        utils.retry_on_exception(
            failing_call,
            exceptions=exceptions,
            retry_count=retry_count,
            retry_delay=retry_delay,
            delay_factor=delay_factor,
            logger=cba_log
        )

    # ensure failing_func() exception was eventually raised
    assert str(exc.value) == error

    # verify that we saw an attempt to call the function
    assert (
        "Attempting to run '%s'" % failing_call.func.__name__
    ) in caplog.text

    # verify that the exception was caught
    assert (
        "Caught exception: %s" % error
    ) in caplog.text

    # verify that all expected retries occurred
    for i in range(retry_count, 0, -1):
        assert (
            "%s, retry after %g second%s, %d attempt%s remaining..." % (
                error,
                retry_delay,
                '',
                i,
                's' if i != 1 else ''
            )
        ) in caplog.text

    # verify that exhaustion of retries occurred
    assert (
        "Retries exhausted, re-raising: %s" % error
    ) in caplog.text


def test_retry_on_exception_param_corrections(caplog):
    """Verify invalid parameter correct logic."""

    message = "Mock testing"

    succeeding_call = functools.partial(succeeding_func, message)

    check_params = [
        ('retry_count', 0, 1),
        ('retry_count', -1, 1),
        ('retry_delay', 0, 1),
        ('retry_delay', -0.1, 0.1),
        ('delay_factor', 0, 1),
        ('delay_factor', -1, 1)
    ]

    for param, bad_value, corrected_value in check_params:

        # test succeeding_call with param that needs correction
        result = utils.retry_on_exception(
            **{
                "func_call": succeeding_call,
                param: bad_value
            }
        )

        # ensure expected value was returned
        assert result == message

        # ensure param was corrected
        assert (
            "Specified %s %g corrected to %g" % (
                param,
                bad_value,
                corrected_value
            )
        ) in caplog.text


def test_retry_on_exception_func_name(caplog):
    """Verify correct handling for func_name param."""

    message = "Mock testing"
    func_name = "MockTesting"

    succeeding_call = functools.partial(succeeding_func, message)

    # test succeeding_call
    result = utils.retry_on_exception(
        succeeding_call,
        func_name=func_name
    )

    # ensure expected value was returned
    assert result == message

    # verify that we saw an attempt to call the function
    assert (
        "Attempting to run '%s'" % func_name
    ) in caplog.text
