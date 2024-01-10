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
import functools
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
    CSPBillingAdapterException,
    FailedToSaveCSPConfigError
)
from csp_billing_adapter.utils import (
    date_to_string,
    get_now,
    retry_on_exception,
    string_to_date
)
from csp_billing_adapter.bill_utils import process_metering
from csp_billing_adapter import (
    csp_hookspecs,
    hookspecs,
    storage_hookspecs,
    archive_hookspecs,
    hookimpls
)

LOGGER_NAME = 'CSPBillingAdapter'
LOGGING_FORMAT = '%(asctime)s.%(msecs)03d|%(levelname)s|%(name)s|%(message)s'
LOGGING_DATE_FMT = '%Y-%m-%dT%H:%M:%S'
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
    pm.add_hookspecs(archive_hookspecs)
    pm.register(hookimpls)
    pm.load_setuptools_entrypoints('csp_billing_adapter')
    return pm


def setup_logging() -> logging.Logger:
    """Setup basic logging"""
    logging.basicConfig(
        format=LOGGING_FORMAT,
        datefmt=LOGGING_DATE_FMT
    )
    log = logging.getLogger(LOGGER_NAME)
    log.setLevel(logging.INFO)
    logging.Formatter.converter = time.gmtime

    log.info(f"{LOGGER_NAME} logging setup complete")
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


def update_logger_from_config(config: Config, log: logging.Logger):
    """Update the logger based on configuration file options."""
    current_level = log.getEffectiveLevel()
    log.setLevel(config.get('logging', {}).get('level', current_level))

    if current_level != log.getEffectiveLevel():
        log.info(
            f"{LOGGER_NAME} logging level updated to {log.getEffectiveLevel()}"
        )


def initial_adapter_setup(
    hook,
    config: Config,
    log: logging.Logger
) -> (dict, dict):
    """Initial setup before starting event loop."""

    log.debug("Setting up the adapter via hook")
    retry_on_exception(
        functools.partial(
            hook.setup_adapter,
            config=config
        ),
        logger=log,
        func_name="hook.setup_adapter"
    )

    log.debug("Initializing the csp_config")
    try:
        csp_config = retry_on_exception(
            functools.partial(
                hook.get_csp_config,
                config=config
            ),
            logger=log,
            func_name="hook.get_csp_config"
        )
    except Exception as e:
        log.debug(
            "Failed to retrieve existing CSP config: %s",
            str(e)
        )
        csp_config = {}

    if not csp_config:
        account_info = retry_on_exception(
            functools.partial(
                hook.get_account_info,
                config=config
            ),
            logger=log,
            func_name="hook.get_account_info"
        )

        csp_config = create_csp_config(
            config,
            account_info,
            hook.get_archive_location()
        )

    # Update csp-config with latest plugin versions
    versions = hook.get_version()
    if versions:
        csp_config['versions'] = dict(versions)

    try:
        retry_on_exception(
            functools.partial(
                hook.save_csp_config,
                config=config,
                csp_config=csp_config
            ),
            logger=log,
            func_name="hook.save_csp_config"
        )
    except Exception as exc:
        # raise an application specific exception that will be
        # caught by the event loop in main() and cause an exit
        # with a failure status.
        log.error("Unable to save CSP config: %s", str(exc))
        raise FailedToSaveCSPConfigError(str(exc)) from exc

    log.debug("Initializing the cache")
    try:
        cache = retry_on_exception(
            functools.partial(
                hook.get_cache,
                config=config
            ),
            logger=log,
            func_name="hook.get_cache"
        )
    except Exception as e:
        log.debug(
            "Failed to retrieve existing cache: %s",
            str(e)
        )
        cache = {}

    if not cache:
        cache = create_cache(hook, config)
        initial_deploy = True
    else:
        initial_deploy = False

    log.info("Adapter setup complete")
    return cache, csp_config, initial_deploy


def event_loop_handler(
    hook,
    config: Config,
    log: logging.Logger,
    now: datetime.datetime,
    cache: dict,
    csp_config: dict
) -> None:
    """Perform the event loop processing actions."""
    log.info('Starting event loop processing')
    csp_config['errors'] = []

    try:
        usage = retry_on_exception(
            functools.partial(
                hook.get_usage_data,
                config=config
            ),
            logger=log,
            func_name="hook.get_usage_data"
        )
        log.debug('Retrieved usage data: %s', usage)
    except Exception as exc:
        usage = None
        log.warning("Failed to retrieve usage data: %s", str(exc))
        csp_config['errors'].append(f'Usage data retrieval failed: {exc}')

    if usage:
        add_usage_record(usage, cache, config.billing_interval)
        csp_config['base_product'] = usage.get('base_product', '')

    log.debug(
        "Now: %s, Next Reporting Time: %s, Next Bill Time: %s",
        date_to_string(now),
        cache['next_reporting_time'],
        cache['next_bill_time']
    )

    if now >= string_to_date(cache['next_bill_time']):
        log.info('Attempt a billing cycle update')
        process_metering(
            hook,
            config,
            now,
            cache,
            csp_config
        )
    elif now >= string_to_date(cache['next_reporting_time']):
        log.info('Attempt a reporting cycle update')
        process_metering(
            hook,
            config,
            now,
            cache,
            csp_config,
            empty_metering=True
        )

    # Backup cache to datastore

    log.info("Updating cache with: %s", cache)
    try:
        retry_on_exception(
            functools.partial(
                hook.update_cache,
                config=config,
                cache=cache,
                replace=False
            ),
            logger=log,
            func_name="hook.update_cache"
        )
    except Exception as error:
        log.warning("Failed to save cache to datastore: %s", str(error))
        csp_config['errors'].append(f'Cache failed to save: {error}')

    csp_config['timestamp'] = date_to_string(now)

    # Backup csp-config to datastore

    log.info("Updating CSP config with: %s", csp_config)
    try:
        retry_on_exception(
            functools.partial(
                hook.update_csp_config,
                config=config,
                csp_config=csp_config,
                replace=False
            ),
            logger=log,
            func_name="hook.update_csp_config"
        )
    except Exception as error:
        log.warning("Failed to save csp_config to datastore: %s", str(error))
        csp_config['errors'].append(f'csp_config failed to save: {error}')

    log.info('Finishing event loop processing')


def metering_test(
    hook,
    config: Config,
    log: logging.Logger,
    csp_config: dict
) -> None:
    """
    Perform a dry-run metering operation to test that metering is supported
    by submitting a random dimension with a metric of 0.
    """
    # catch any exceptions raised by the metering test, attempting
    # to update the csp_config with the error encountered.
    try:

        # perform the metering test, catching and re-raising any
        # handled exceptions appropriately.
        try:
            metric = next(iter(config.usage_metrics))
            dimension = next(iter(
                config.usage_metrics[metric]['dimensions']
            ))['dimension']

            retry_on_exception(
                functools.partial(
                    hook.meter_billing,
                    config=config,
                    dimensions={dimension: 0},
                    timestamp=get_now(),
                    dry_run=True
                ),
                logger=log,
                func_name="hook.meter_billing"
            )
        except AttributeError as attr_error:
            raise CSPBillingAdapterException(
                f'Billing adapter config is invalid. {attr_error}'
            )
        except KeyError as key:
            raise CSPBillingAdapterException(
                f'Billing adapter config is invalid. Config is missing {key}'
            )
        except Exception as error:
            raise CSPBillingAdapterException(
                f'Fatal error while validating metering API access: {error}'
            )

    except Exception as error:
        err_msg = f'Metering test failed: {error}'
        csp_config['errors'].append(err_msg)
        log.error(err_msg)
        log.info("Updating CSP config with: %s", csp_config)

        try:
            retry_on_exception(
                functools.partial(
                    hook.update_csp_config,
                    config=config,
                    csp_config=csp_config,
                    replace=False
                ),
                logger=log,
                func_name="hook.update_csp_config"
            )
        except Exception as update_csp_error:
            log.error(
                "Failed to save csp_config to datastore: %s",
                str(update_csp_error)
            )

        raise


def main() -> None:
    """
    Main routine, implementing the event loop for the csp_billing_adapter.
    """
    pm = get_plugin_manager()

    try:
        log = setup_logging()

        config = get_config(
            config_path,
            pm.hook,
            log
        )

        update_logger_from_config(config, log)

        cache, csp_config, initial_deploy = initial_adapter_setup(
            pm.hook,
            config,
            log
        )

        metering_test(pm.hook, config, log, csp_config)

        if initial_deploy:
            time.sleep(config.query_interval)  # wait 1 cycle for usage data

        while True:
            start = get_now()
            event_loop_handler(
                pm.hook,
                config,
                log,
                start,
                cache,
                csp_config
            )
            log.info("Processed event loop at %s", date_to_string(start))

            query_interval_remainder = (
                config.query_interval - (get_now() - start).total_seconds()
            )
            log.debug("Sleeping for %g seconds", query_interval_remainder)
            time.sleep(query_interval_remainder)
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
    main()  # pragma: no cover
