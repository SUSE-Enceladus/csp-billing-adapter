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

from random import randrange
from datetime import datetime

import csp_billing_adapter

from csp_billing_adapter.config import Config

log = logging.getLogger('CSPBillingAdapter')


@csp_billing_adapter.hookimpl(trylast=True)
def meter_billing(
    config: Config,
    dimensions: dict,
    timestamp: datetime,
    dry_run: bool,
    customer_id: str = None
) -> dict:
    """Simulate a CSP metering operation with a 5% chance of failure."""
    log.info('Mock CSP received metering of: %s', dimensions)
    seed = randrange(40)
    status = {}

    if seed == 4:
        log.warning("Simulating failed metering operation")
        raise Exception('Unable to submit meter usage. Payment not billed!')
    elif seed == 14:
        log.warning('Simulating failed metering operation')
        for dimension, quantity in dimensions.items():
            status[dimension] = {
                'error': 'Simulating failed metering operation',
                'status': 'failed'
            }
    elif seed == 24:
        log.info('Simulating legacy return type')
        status = str(uuid.uuid4().hex)
    else:
        for dimension, quantity in dimensions.items():
            status[dimension] = {
                'record_id': str(uuid.uuid4().hex),
                'status': 'succeeded'
            }

    return status


@csp_billing_adapter.hookimpl(trylast=True)
def get_csp_name(config: Config) -> str:
    """Return the 'local' CSP's name."""
    return 'local'


@csp_billing_adapter.hookimpl(trylast=True)
def get_account_info(config: Config) -> str:
    """Return the 'local' CSP's account info."""
    return {
        'account_id': '123456789',
        'arch': 'x86_64',
        'cloud_provider': 'local'
    }


@csp_billing_adapter.hookimpl
def get_version():
    version = csp_billing_adapter.__version__
    return ('test_csp_plugin', version)
