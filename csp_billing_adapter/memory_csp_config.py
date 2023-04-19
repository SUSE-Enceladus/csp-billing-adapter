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

import logging

import csp_billing_adapter

from csp_billing_adapter.config import Config

memory_csp_config = {}

log = logging.getLogger('CSPBillingAdapter')


@csp_billing_adapter.hookimpl(trylast=True)
def get_csp_config(config: Config):
    """Retrieve csp_config content from in-memory csp_config."""

    log.info("Retrieved CSP Config Content: %s", memory_csp_config)

    return {**memory_csp_config}


@csp_billing_adapter.hookimpl(trylast=True)
def update_csp_config(config: Config, csp_config: dict, replace: bool):
    """
    Update in-memory csp_config with new content, replacing if specified.
    """

    global memory_csp_config

    if replace:
        old_csp_config = {}
    else:
        old_csp_config = memory_csp_config

    memory_csp_config = {**old_csp_config, **csp_config}

    log.info("Updated CSP Config Content: %s", memory_csp_config)


@csp_billing_adapter.hookimpl(trylast=True)
def save_csp_config(config: Config, csp_config: dict):
    """Save specified content as new in-memory csp_config contents."""

    update_csp_config(config, csp_config, replace=True)
