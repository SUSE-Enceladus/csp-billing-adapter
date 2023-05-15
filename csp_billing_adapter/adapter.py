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

import datetime
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
from csp_billing_adapter.exceptions import (
    CSPBillingAdapterException
)
from csp_billing_adapter.utils import (
    date_to_string,
    string_to_date
)
from csp_billing_adapter.bill_utils import process_metering
from csp_billing_adapter import (
    csp_hookspecs,
    hookspecs,
    storage_hookspecs
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
    return pm


def setup_logging(hook) -> logging.Logger:
    """Setup basic logging"""
    logging.basicConfig()
    log = logging.getLogger('CSPBillingAdapter')
    log.setLevel(logging.INFO)

    log.info("CSPBillingAdapter logging setup complete")
    return log


def get_config(
    config_path,
    hook,
    log: logging.Logger
) -> Config:
    """Load the specified config file."""

    config = Config.load_from_file(
        config_path,
        hook
    )

    # If there is anything sensitive in config we may want to add
    # a __str__() method that sanitizes it.
    log.info("Config loaded: %s", config)

    return config


def initial_adapter_setup(
    hook,
    config: Config,
    log: logging.Logger
) -> None:
    """Initial setup before starting event loop."""

    log.debug("Setting up the adapter via hook")
    hook.setup_adapter(config=config)

    log.debug("Initializing the csp_config")
    try:
        csp_config = hook.get_csp_config(config=config)
    except Exception as e:
        log.warning(
            "Failed to retrieve existing CSP config: %s",
            str(e)
        )
        csp_config = {}

    if not csp_config:
        csp_config = create_csp_config(hook, config)

    log.debug("Initializing the cache")
    try:
        cache = hook.get_cache(config=config)
    except Exception as e:
        log.warning(
            "Failed to retrieve existing cache: %s",
            str(e)
        )
        cache = {}

    if not cache:
        cache = create_cache(hook, config)

    log.info("Adapter setup complete")
    return cache, csp_config


def event_loop_handler(
    hook,
    config: Config,
    log: logging.Logger,
    now: datetime.datetime,
    cache: dict,
    csp_config: dict
) -> datetime.datetime:
    """Perform the event loop processing actions."""
    log.info('Starting event loop processing')
    errors = []

    try:
        usage = hook.get_usage_data(config=config)
        log.debug('Retrieved usage data: %s', usage)
    except Exception as exc:
        log.warning("Failed to retrieve usage data: %s", str(exc))
        errors.append(f'Usage data retrieval failed: {exc}')

    if usage:
        add_usage_record(usage, cache)

    log.debug(
        "Now: %s, Next Reporting Time: %s, Next Bill Time: %s",
        date_to_string(now),
        cache['next_reporting_time'],
        cache['next_bill_time']
    )

    if now >= string_to_date(cache['next_bill_time']):
        log.info('Attempt a billing cycle update')
        errors += process_metering(
            hook,
            config,
            now,
            cache,
            csp_config
        )
    elif now >= string_to_date(cache['next_reporting_time']):
        log.info('Attempt a reporting cycle update')
        errors += process_metering(
            hook,
            config,
            now,
            cache,
            csp_config,
            empty_metering=True
        )

    csp_config['timestamp'] = date_to_string(now),
    csp_config['errors'] = errors

    log.info("Updating CSP config with: %s", csp_config)
    try:
        hook.update_csp_config(
            config=config,
            csp_config=csp_config,
            replace=False
        )
    except Exception as error:
        log.warning("Failed to save csp_config to datastore: %s", str(error))
        errors.append(f'csp_config failed to save: {error}')

    log.info("Updating cache with: %s", cache)
    try:
        hook.update_cache(
            config=config,
            cache=cache,
            replace=False
        )
    except Exception as error:
        log.warning("Failed to save cache to datastore: %s", str(error))
        errors.append(f'Cache failed to save: {error}')

    log.info('Finishing event loop processing')


def main() -> None:
    """
    Main routine, implementing the event loop for the csp_billing_adapter.
    """
    pm = get_plugin_manager()

    try:
        log = setup_logging(pm.hook)

        config = get_config(
            config_path,
            pm.hook,
            log
        )

        cache, csp_config = initial_adapter_setup(pm.hook, config, log)

        try:
            # Test metering API access with random dimension metric
            metric = next(iter(config.usage_metrics))
            dimension = next(iter(
                config.usage_metrics[metric]['dimensions']
            ))['dimension']

            pm.hook.meter_billing(
                config=config,
                dimensions={dimension: 0},
                timestamp=csp_config['timestamp'],
                dry_run=True
            )
        except KeyError as key:
            raise CSPBillingAdapterException(
                f'Billing adapter config is invalid. Config is missing {key}'
            )
        except Exception as error:
            raise CSPBillingAdapterException(
                f'Fatal error while validating metering API access: {error}'
            )

        time.sleep(config.query_interval)  # wait 1 cycle for usage data

        while True:
            now = event_loop_handler(
                pm.hook,
                config,
                log,
                cache,
                csp_config
            )
            log.info("Processed event loop at %s", date_to_string(now))

            log.debug("Sleeping for %d seconds", config.query_interval)
            time.sleep(config.query_interval)
    except KeyboardInterrupt:
        sys.exit(0)
    except SystemExit as e:
        # user exception, program aborted by user
        sys.exit(e)
    except CSPBillingAdapterException as e:
        # csp_billing_adapter specific exception
        log.error('CSP Billing Adapter error: {0}'.format(e))
        traceback.print_exc()
        sys.exit(2)
    except Exception as e:
        # exception we did no expect, show python backtrace
        log.error('Unexpected error: {0}'.format(e))
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
