import logging
import os
import sys
import time
import traceback

import pluggy

from csp_billing_adapter.config import Config
from csp_billing_adapter.csp_cache import (
    add_usage_record,
    cache_meter_record,
    create_cache,
    get_billing_dimensions,
    get_billable_usage
)
from csp_billing_adapter.csp_config import (
    create_csp_config,
)
from csp_billing_adapter.utils import get_now, date_to_string
from csp_billing_adapter import hookspecs
from csp_billing_adapter import local_csp, product_api

namespace = 'neuvector-csp-billing-adapter'


def get_plugin_manager():
    pm = pluggy.PluginManager('csp_billing_adapter')
    pm.add_hookspecs(hookspecs)
    pm.load_setuptools_entrypoints('csp_billing_adapter')
    pm.register(local_csp)
    pm.register(product_api)
    return pm


def main():
    pm = get_plugin_manager()

    try:
        logging.basicConfig()
        log = logging.getLogger('CSPBillingAdapter')
        log.setLevel(logging.INFO)

        config = Config.load_from_file(
            os.path.expanduser('~/.config/csp-billing-adapter.yaml'),
            pm.hook
        )
        pm.hook.setup_adapter(config=config)

        csp_config = pm.hook.get_csp_config(config=config)
        if not csp_config:
            create_csp_config(
                pm.hook,
                config,
            )

        cache = pm.hook.get_cache(config=config)
        if not cache:
            create_cache(pm.hook, config)

        while True:
            usage = pm.hook.get_usage_data(config=config)
            add_usage_record(pm.hook, config, usage)

            now = get_now()
            mins = now.strftime('%M')
            if mins.endswith('3'):
                cache = pm.hook.get_cache(config=config)
                billable_usage = get_billable_usage(
                    cache.get('usage_records', []),
                    config
                )
                dimensions = get_billing_dimensions(config, billable_usage)

                try:
                    record_id = pm.hook.meter_billing(
                        config=config,
                        dimensions=dimensions,
                        timestamp=date_to_string(get_now())
                    )
                except Exception as e:
                    pm.hook.update_csp_config(
                        config=config,
                        csp_config={
                            'billed': False,
                            'error': str(e)
                        }
                    )
                else:
                    cache_meter_record(
                        pm.hook,
                        config,
                        record_id,
                        dimensions,
                        timestamp=date_to_string(now),
                    )
                    pm.hook.update_csp_config(
                        config=config,
                        csp_config={
                            'billed': True,
                            'usage': billable_usage,
                            'error': ''
                        }
                    )

            time.sleep(60)
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