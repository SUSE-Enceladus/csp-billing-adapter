#
# Unit tests for the csp_billing_adapter.memory_cache when called via hooks
#

def test_memory_get_cache(cba_pm, cba_config):
    # cache should initially be empty
    assert cba_pm.hook.get_cache(config=cba_config) == {}


def test_memory_cache_update_merge(cba_pm, cba_config):
    test_data1 = dict(a=1, b=2)
    test_data2 = dict(a=10, c=12)
    test_data3 = {**test_data1, **test_data2}

    # cache should initially be empty
    assert cba_pm.hook.get_cache(config=cba_config) == {}

    cba_pm.hook.update_cache(
        config=cba_config,
        cache=test_data1,
        replace=False
    )

    assert cba_pm.hook.get_cache(config=cba_config) == test_data1

    cba_pm.hook.update_cache(
        config=cba_config,
        cache=test_data2,
        replace=False
    )

    assert cba_pm.hook.get_cache(config=cba_config)['a'] != test_data1['a']
    assert cba_pm.hook.get_cache(config=cba_config)['b'] == test_data1['b']
    assert cba_pm.hook.get_cache(config=cba_config)['c'] == test_data2['c']
    assert cba_pm.hook.get_cache(config=cba_config) == test_data3


def test_memory_cache_update_replace(cba_pm, cba_config):
    test_data1 = dict(a=1, b=2)
    test_data2 = dict(c=3, d=4)

    # cache should initially be empty
    assert cba_pm.hook.get_cache(config=cba_config) == {}

    cba_pm.hook.update_cache(
        config=cba_config,
        cache=test_data1,
        replace=False
    )

    assert cba_pm.hook.get_cache(config=cba_config) == test_data1

    cba_pm.hook.update_cache(
        config=cba_config,
        cache=test_data2,
        replace=True
    )

    assert cba_pm.hook.get_cache(config=cba_config) == test_data2


def test_memory_cache_save(cba_pm, cba_config):
    test_data1 = dict(a=1, b=2)
    test_data2 = dict(c=3, d=4)

    # cache should initially be empty
    assert cba_pm.hook.get_cache(config=cba_config) == {}

    cba_pm.hook.save_cache(config=cba_config, cache=test_data1)

    assert cba_pm.hook.get_cache(config=cba_config) == test_data1

    cba_pm.hook.save_cache(config=cba_config, cache=test_data2)

    assert cba_pm.hook.get_cache(config=cba_config) == test_data2
