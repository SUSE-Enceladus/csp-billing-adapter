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

"""Core event loop for csp-billing-adapter."""

import logging
import os
import sys
import time
import traceback

import pluggy

from csp_billing_adapter.config import Config
from csp_billing_adapter.csp_cache import (
    add_usage_record,
    create_cache
)
from csp_billing_adapter.csp_config import (
    create_csp_config,
)
from csp_billing_adapter.utils import get_now, string_to_date
from csp_billing_adapter.bill_utils import process_metering
from csp_billing_adapter import hookspecs
from csp_billing_adapter import csp_hookspecs
from csp_billing_adapter import storage_hookspecs
from csp_billing_adapter import (
    local_csp,
)

DEFAULT_CONFIG_PATH = '/etc/csp_billing_adapter/config.yaml'

config_path = os.environ.get('CSP_ADAPTER_CONFIG_FILE') or DEFAULT_CONFIG_PATH


def get_plugin_manager() -> pluggy.PluginManager:
    """
    Creates a PluginManager instance for the 'csp_billing_adapter', setting
    it up appropriately.

    :return: Return a configured pluggy.PluginManager instance
    """
    pm = pluggy.PluginManager('csp_billing_adapter')
    pm.add_hookspecs(hookspecs)
    pm.add_hookspecs(csp_hookspecs)
    pm.add_hookspecs(storage_hookspecs)
    pm.load_setuptools_entrypoints('csp_billing_adapter')
    pm.register(local_csp)
    return pm


def main() -> None:
    """
    Main routine, implementing the event loop for the csp_billing_adapter.
    """
    pm = get_plugin_manager()

    try:
        logging.basicConfig()
        log = logging.getLogger('CSPBillingAdapter')
        log.setLevel(logging.INFO)

        config = Config.load_from_file(
            config_path,
            pm.hook
        )

        pm.hook.setup_adapter(config=config)

        csp_config = pm.hook.get_csp_config(config=config)
        if not csp_config:
            create_csp_config(pm.hook, config)

        cache = pm.hook.get_cache(config=config)
        if not cache:
            create_cache(pm.hook, config)

        while True:
            usage = pm.hook.get_usage_data(config=config)
            add_usage_record(pm.hook, config, usage)

            cache = pm.hook.get_cache(config=config)
            now = get_now()

            if now >= string_to_date(cache['next_bill_time']):
                process_metering(config, cache, pm.hook)
            elif now >= string_to_date(cache['next_reporting_time']):
                process_metering(config, cache, pm.hook, empty_metering=True)

            time.sleep(config.query_interval)
    except KeyboardInterrupt:
        sys.exit(0)
    except SystemExit as e:
        # user exception, program aborted by user
        sys.exit(e)
    except Exception as e:
        # exception we did no expect, show python backtrace
        log.error('Unexpected error: {0}'.format(e))
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
