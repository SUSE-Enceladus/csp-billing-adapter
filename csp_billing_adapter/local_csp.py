import csp_billing_adapter

from csp_billing_adapter.config import Config

from random import randrange


@csp_billing_adapter.hookimpl(trylast=True)
def meter_billing(
    config: Config,
    dimensions: dict,
    timestamp: str,
):
    seed = randrange(10)

    if seed == 4:
        raise Exception('Unable to submit meter usage. Payment not billed!')
    else:
        return '1234567890'


@csp_billing_adapter.hookimpl(trylast=True)
def get_csp_name(config: Config):
    return 'local'


@csp_billing_adapter.hookimpl(trylast=True)
def get_account_info(config: Config):
    return {'account_number': '123456789'}
