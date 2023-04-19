import pathlib
import yaml

import pytest

from csp_billing_adapter.adapter import get_plugin_manager


def pytest_configure(config):
    """Custom pytest configuration."""

    # configure custom markers
    config.addinivalue_line(
        "markers", ('config: the config file path to load')
    )


@pytest.fixture(scope="session")
def data_dir(pytestconfig):
    """
    Fixture returning the path to the data directory under the tests
    area for this pytest run.
    """
    # Get testing root directory, supporting older versions of
    # pytest that don't have rootpath
    if hasattr(pytestconfig, 'rootpath'):
        testroot = pytestconfig.rootpath
    else:
        testroot = pathlib.Path(pytestconfig.rootdir)

    return testroot / "tests/data"


@pytest.fixture
def cba_config(data_dir, request):
    """
    Fixture returning a config dictionary loaded from the config
    file specified by the config marker, defaulting to a known
    good config if none is provided.
    """
    config_marker = request.node.get_closest_marker('config')
    if config_marker:
        config_file = config_marker.args[0]
    else:
        config_file = 'config_good.yaml'

    config_path = data_dir / config_file

    return yaml.safe_load(config_path.open())


@pytest.fixture
def cba_pm(cba_config):
    """
    Fixture returning an initialized plugin manager instance, based
    on supplied config. Also needs to reset the in-memory cache and
    csp_config to empty to simulate a fresh start.
    """
    pm = get_plugin_manager()

    # reset the in-memory cache to empty
    pm.hook.save_cache(config=cba_config, cache=dict())

    # reset the in-memory csp_config to empty
    pm.hook.save_csp_config(config=cba_config, csp_config=dict())

    return pm
