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

"""Pluggy hook interface specifications for storage related functionality."""

import pluggy

from csp_billing_adapter.config import Config

hookspec = pluggy.HookspecMarker('csp_billing_adapter')


@hookspec(firstresult=True)
def get_csp_config(config: Config) -> None:
    """
    Retrieves the CSP Support Config from stateful storage

    :param config: The application configuration dictionary
    :return: Return a hash of the CSP Support Config
    """


@hookspec(firstresult=True)
def save_csp_config(config: Config, csp_config: Config) -> None:
    """
    Saves the CSP Support Config to stateful storage

    :param config: The application configuration dictionary
    :param csp_config: The CSP Support Config dictionary
    """


@hookspec(firstresult=True)
def update_csp_config(
    config: Config,
    csp_config: Config,
    replace: bool
) -> None:
    """
    Update or replace the CSP Support Config in stateful storage

    :param config: The application configuration dictionary
    :param csp_config: The CSP Support Config dictionary
    :param replace: If True the dictionary is replaced not updated
    """


@hookspec(firstresult=True)
def get_cache(config: Config) -> None:
    """
    Retrieves the CSP Adapter Cache from stateful storage

    :param config: The application configuration dictionary
    :return: Return a hash of the CSP Adapter Cache
    """


@hookspec(firstresult=True)
def save_cache(config: Config, cache: dict) -> None:
    """
    Saves the CSP Adapter Cache to stateful storage

    :param config: The application configuration dictionary
    :param cache: The CSP Adapter Cache dictionary
    """


@hookspec(firstresult=True)
def update_cache(config: Config, cache: dict, replace: bool) -> None:
    """
    Update or replace CSP Adapter Cache in stateful storage

    :param config: The application configuration dictionary
    :param cache: The CSP Adapter Cache dictionary
    :param replace: If True the cache is replaced not updated
    """
