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
from unittest import mock

from pytest import raises

from csp_billing_adapter.csp_config import create_csp_config
from csp_billing_adapter.exceptions import (
    FailedToSaveCSPConfigError
)
from csp_billing_adapter.utils import string_to_date


def test_create_csp_config(cba_pm, cba_config):
    # csp_config should initially be empty
    assert cba_pm.hook.get_csp_config(config=cba_config) == {}

    new_csp_config = create_csp_config(cba_pm.hook, cba_config)

    csp_config = cba_pm.hook.get_csp_config(config=cba_config)

    assert 'billing_api_access_ok' in csp_config
    assert csp_config['billing_api_access_ok'] is True
    assert 'timestamp' in csp_config
    assert 'expire' in csp_config

    assert new_csp_config == csp_config

    timestamp = string_to_date(csp_config['timestamp'])
    expire = string_to_date(csp_config['expire'])
    delta = datetime.timedelta(seconds=cba_config.reporting_interval)

    assert timestamp + delta == expire


def test_create_csp_config_save_exception(cba_pm, cba_config, caplog):
    # csp_config should initially be empty
    assert cba_pm.hook.get_csp_config(config=cba_config) == {}

    # simulate save_csp_cache() hook raising an exception
    error = Exception("Simulated save_csp_cache() hook Exception")
    with mock.patch.object(
        cba_pm.hook,
        'save_csp_config',
        side_effect=error
    ):
        with raises(FailedToSaveCSPConfigError):
            create_csp_config(cba_pm.hook, cba_config)
        assert str(error) in caplog.text
