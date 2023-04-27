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
# Unit tests for the csp_billing_adapter.memory_csp_config when called
# via hooks
#

def test_memory_get_csp_config(cba_pm, cba_config):
    # csp_config should initially be empty
    assert cba_pm.hook.get_csp_config(config=cba_config) == {}


def test_memory_csp_config_update_merge(cba_pm, cba_config):
    test_data1 = dict(a=1, b=2)
    test_data2 = dict(a=10, c=12)
    test_data3 = {**test_data1, **test_data2}

    # csp_config should initially be empty
    assert cba_pm.hook.get_csp_config(config=cba_config) == {}

    cba_pm.hook.update_csp_config(
        config=cba_config,
        csp_config=test_data1,
        replace=False
    )

    assert cba_pm.hook.get_csp_config(config=cba_config) == test_data1

    cba_pm.hook.update_csp_config(
        config=cba_config,
        csp_config=test_data2,
        replace=False
    )

    csp_config = cba_pm.hook.get_csp_config(config=cba_config)

    assert csp_config['a'] != test_data1['a']
    assert csp_config['b'] == test_data1['b']
    assert csp_config['c'] == test_data2['c']
    assert csp_config == test_data3


def test_memory_csp_config_update_replace(cba_pm, cba_config):
    test_data1 = dict(a=1, b=2)
    test_data2 = dict(c=3, d=4)

    # csp_config should initially be empty
    assert cba_pm.hook.get_csp_config(config=cba_config) == {}

    cba_pm.hook.update_csp_config(
        config=cba_config,
        csp_config=test_data1,
        replace=False
    )

    assert cba_pm.hook.get_csp_config(config=cba_config) == test_data1

    cba_pm.hook.update_csp_config(
        config=cba_config,
        csp_config=test_data2,
        replace=True
    )

    assert cba_pm.hook.get_csp_config(config=cba_config) == test_data2


def test_memory_csp_config_save(cba_pm, cba_config):
    test_data1 = dict(a=1, b=2)
    test_data2 = dict(c=3, d=4)

    # csp_config should initially be empty
    assert cba_pm.hook.get_csp_config(config=cba_config) == {}

    cba_pm.hook.save_csp_config(config=cba_config, csp_config=test_data1)

    assert cba_pm.hook.get_csp_config(config=cba_config) == test_data1

    cba_pm.hook.save_csp_config(config=cba_config, csp_config=test_data2)

    assert cba_pm.hook.get_csp_config(config=cba_config) == test_data2
