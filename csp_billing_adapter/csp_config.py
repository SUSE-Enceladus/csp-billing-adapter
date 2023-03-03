from csp_billing_adapter.config import Config
from csp_billing_adapter.utils import get_now, date_to_string, get_date_delta


def create_csp_config(
    hook,
    config: Config,
):
    now = get_now()
    expire = date_to_string(get_date_delta(now, config.metering_interval))

    csp_config = {
        'billed': True,
        'timestamp': date_to_string(now),
        'expire': expire
    }

    hook.save_csp_config(config=config, csp_config=csp_config)
