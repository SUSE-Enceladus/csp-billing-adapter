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
High-level (implementation agnostic) CSP config operations that
leverage Pluggy hooks to perform the implementation specific
low-level CSP config management operations.
"""

import logging

from csp_billing_adapter.config import Config
from csp_billing_adapter.exceptions import (
    FailedToSaveCSPConfigError
)
from csp_billing_adapter.utils import get_now, date_to_string, get_date_delta

log = logging.getLogger('CSPBillingAdapter')


def create_csp_config(
    hook,
    config: Config,
) -> dict:
    """
    Initialize the csp_config data store.

    :param hook:
        The Pluggy plugin manager hook used to call the save_csp_cache()
        operation.
    :param config:
        The configuration settings associated with the CSP.
    """
    now = get_now()
    expire = date_to_string(get_date_delta(now, config.reporting_interval))

    csp_config = {
        'billing_api_access_ok': True,
        'timestamp': date_to_string(now),
        'expire': expire,
        'customer_csp_data': hook.get_account_info(config=config),
        'errors': []
    }

    try:
        hook.save_csp_config(config=config, csp_config=csp_config)
    except Exception as exc:
        # raise an application specific exception that will be
        # caught by the event loop in main() and cause an exit
        # with a failure status.
        log.error("Unable to save CSP config: %s", str(exc))
        raise FailedToSaveCSPConfigError(str(exc)) from exc

    log.debug("CSP config initialized with: %s", csp_config)
    return csp_config
