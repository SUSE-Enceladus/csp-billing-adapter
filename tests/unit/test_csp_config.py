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
# Unit tests for the csp_billing_adapter.csp_config
#

import datetime
import pytest

from csp_billing_adapter.csp_config import create_csp_config
from csp_billing_adapter.utils import string_to_date


def test_create_csp_config(cba_config):
    account_info = {'name': 'account1', 'id': '1234567890'}
    archive_location = '/tmp/fake_archive.json'
    new_csp_config = create_csp_config(
        cba_config,
        account_info,
        archive_location
    )

    assert 'billing_api_access_ok' in new_csp_config
    assert new_csp_config['billing_api_access_ok'] is True
    assert 'timestamp' in new_csp_config
    assert 'customer_csp_data' in new_csp_config
    assert new_csp_config['customer_csp_data'] == account_info
    assert 'expire' in new_csp_config

    timestamp = string_to_date(new_csp_config['timestamp'])
    expire = string_to_date(new_csp_config['expire'])
    delta = datetime.timedelta(seconds=cba_config.reporting_interval)

    assert timestamp + delta == expire


@pytest.mark.config('config_good_fixed.yaml')
def test_create_csp_config_fixed_billing(cba_config):
    account_info = {'name': 'account1', 'id': '1234567890'}
    archive_location = '/tmp/fake_archive.json'
    new_csp_config = create_csp_config(
        cba_config,
        account_info,
        archive_location
    )

    assert new_csp_config['expire'] == '2030-01-01T00:00:00+00:00'
