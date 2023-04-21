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
