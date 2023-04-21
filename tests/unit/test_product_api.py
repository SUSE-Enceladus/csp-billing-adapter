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
# Unit tests for the csp_billing_adapter.product_api
#

from csp_billing_adapter.product_api import get_usage_data


def test_memory_get_cache(cba_config):
    possible_node_counts = [9, 10, 11, 25]

    usage = get_usage_data(cba_config)

    assert 'managed_node_count' in usage
    assert usage['managed_node_count'] in possible_node_counts
    assert 'reporting_time' in usage
