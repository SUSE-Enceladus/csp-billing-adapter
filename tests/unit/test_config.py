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
test_config.py is part of csp-billing-adapter and provides units tests
for the Config class.
"""
from pytest import raises
from yaml.parser import ParserError

from csp_billing_adapter.config import Config
from csp_billing_adapter.adapter import get_plugin_manager

good_config_file = 'tests/data/config_good_average.yaml'
bad_config_file = 'tests/data/config_bad.yaml'
missing_config_file = 'tests/data/config_missing.yaml'
pm = get_plugin_manager()


def test_get_config_from_good_config_file():
    """Test reading a config file from the specified location."""

    config = Config.load_from_file(
        good_config_file,
        pm.hook
    )
    assert config.get('version') == '0.1.1'
    assert config.product_code == 'foo'


def test_get_config_from_missing_config_file():
    """Test reading a config file that does not exist"""

    with raises(FileNotFoundError):
        Config.load_from_file(
            missing_config_file,
            pm.hook
        )


def test_get_config_from_bad_config_file():
    """Test reading a config file with invalid yaml formatting"""

    with raises(ParserError):
        Config.load_from_file(
            bad_config_file,
            pm.hook
        )
