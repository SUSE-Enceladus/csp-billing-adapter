import pluggy

from csp_billing_adapter.config import Config

hookspec = pluggy.HookspecMarker('csp_billing_adapter')


@hookspec
def setup_adapter(config: Config):
    """
    Perform any pre-setup.

    :param config: The application configuration dictionary
    """


@hookspec(firstresult=True)
def meter_billing(
    config: Config,
    dimensions: dict,
    timestamp: str,
):
    """
    Process metering request against the CSP API.

    :param config: The application configuration dictionary
    :param dimensions: A hash of the billing dimensions and quantities
    :param timestamp: RFC 3339 compliant date time stamp in UTC
    :return: Metering API call ID.
    """


@hookspec(firstresult=True)
def get_billing_data(
    config: Config,
    start_time,
    end_time
):
    """
    Retrieve billing data from CSP API within between start and end time

    :param config: The application configuration dictionary
    :param start_time: Timestamp for the lower search bound
    :param end_time: Timestamp for the upper search bound
    """


@hookspec(firstresult=True)
def get_csp_name(config: Config):
    """
    Retrieves the CSP name from the loaded plugin

    :param config: The application configuration dictionary
    :return: Returns the CSP name
    """


@hookspec(firstresult=True)
def get_account_info(config: Config):
    """
    Retrieves the account information from the loaded plugin

    :param config: The application configuration dictionary
    :return: Returns a dictionary of the account info from CSP
    """


@hookspec(firstresult=True)
def get_csp_config(config: Config):
    """
    Retrieves the CSP Support Config from stateful storage

    :param config: The application configuration dictionary
    :return: Return a hash of the CSP Support Config
    """


@hookspec(firstresult=True)
def save_csp_config(config: Config, csp_config: Config):
    """
    Saves the CSP Support Config to stateful storage

    :param config: The application configuration dictionary
    :param csp_config: The CSP Support Config dictionary
    """


@hookspec(firstresult=True)
def update_csp_config(config: Config, csp_config: Config, replace: bool = False):
    """
    Update or replace the CSP Support Config in stateful storage

    :param config: The application configuration dictionary
    :param csp_config: The CSP Support Config dictionary
    :param replace: If True the dictionary is replaced not updated
    """


@hookspec(firstresult=True)
def get_cache(config: Config):
    """
    Retrieves the CSP Adapter Cache from stateful storage

    :param config: The application configuration dictionary
    :return: Return a hash of the CSP Adapter Cache
    """


@hookspec(firstresult=True)
def save_cache(config: Config, cache: dict):
    """
    Saves the CSP Adapter Cache to stateful storage

    :param config: The application configuration dictionary
    :param cache: The CSP Adapter Cache dictionary
    """


@hookspec(firstresult=True)
def update_cache(config: Config, cache: dict, replace: bool = False):
    """
    Update or replace CSP Adapter Cache in stateful storage

    :param config: The application configuration dictionary
    :param cache: The CSP Adapter Cache dictionary
    :param replace: If True the cache is replaced not updated
    """


@hookspec(firstresult=True)
def get_usage_data(config: Config):
    """
    Retrieves the current usage report from API

    :param config: The application configuration dictionary
    :return: Return a hash with the current usage report
    """


@hookspec(firstresult=True)
def load_defaults(defaults: dict):
    pass
