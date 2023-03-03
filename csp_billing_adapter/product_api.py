import random

import csp_billing_adapter

from csp_billing_adapter.config import Config
from csp_billing_adapter.csp_usage import Usage
from csp_billing_adapter.utils import get_now, date_to_string


@csp_billing_adapter.hookimpl(trylast=True)
def get_usage_data(config: Config):
    quantity = random.choices(
        [9, 10, 11, 25],
        weights=(.33, .33, .33, .01),
        k=1
    )[0]
    usage = Usage(
        quantity,
        date_to_string(get_now())
    )
    return usage
