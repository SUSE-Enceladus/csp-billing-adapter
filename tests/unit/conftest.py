import pytest

from csp_billing_adapter.adapter import get_plugin_manager


@pytest.fixture
def cba_config():
    """Fixture returning a config dictionary."""
    return dict(version=1, billing_interval=30, metering_interval=30)


@pytest.fixture
def cba_pm(cba_config):
    """
    Fixture returning an initialized plugin manager instance, based
    on supplied config. Also needs to reset the cache to empty to
    simulate a fresh start.
    """
    pm = get_plugin_manager()

    # reset the in-memory cache to empty
    pm.hook.save_cache(config=cba_config, cache=dict())

    return pm
