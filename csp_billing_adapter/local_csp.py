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
Pluggy hook implementations emulating CSP interactions.

Note that the meter_billing can fail with a generic exception raised
5% of the time.
"""

import logging
import uuid

import csp_billing_adapter

from csp_billing_adapter.config import Config

from random import randrange

log = logging.getLogger('CSPBillingAdapter')


@csp_billing_adapter.hookimpl(trylast=True)
def meter_billing(
    config: Config,
    dimensions: dict,
    timestamp: str,
):
    log.warning(f'Mock CSP received metering of: {str(dimensions)}')
    seed = randrange(20)

    if seed == 4:
        raise Exception('Unable to submit meter usage. Payment not billed!')
    else:
        return str(uuid.uuid4().hex)


@csp_billing_adapter.hookimpl(trylast=True)
def get_csp_name(config: Config):
    return 'local'


@csp_billing_adapter.hookimpl(trylast=True)
def get_account_info(config: Config):
    return {'account_number': '123456789'}
