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

"""Pluggy hook implementations emulating CSP usage data retrieval."""

import logging
import random

import csp_billing_adapter

from csp_billing_adapter.config import Config
from csp_billing_adapter.utils import get_now, date_to_string

log = logging.getLogger('CSPBillingAdapter')


@csp_billing_adapter.hookimpl(trylast=True)
def get_usage_data(config: Config) -> dict:
    """
    Simulate a CSP usage data retrieval returning one of four possible
    usage values.
    """

    quantity = random.choices(
        [9, 10, 11, 25],
        weights=(.33, .33, .33, .01),
        k=1
    )[0]

    usage = {
        'managed_node_count': quantity,
        'reporting_time': date_to_string(get_now()),
        'base_product': 'cpe:/o:suse:product:v1.2.3'
    }

    log.info("Simulated Usage data: %s", usage)

    return usage
