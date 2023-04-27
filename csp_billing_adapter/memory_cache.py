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

"""In-memory cache plugin implementation."""

import logging

import csp_billing_adapter

from csp_billing_adapter.config import Config

memory_cache = {}

log = logging.getLogger('CSPBillingAdapter')


@csp_billing_adapter.hookimpl(trylast=True)
def get_cache(config: Config):
    """Retrieve cache content from in-memory cache."""

    log.info("Retrieved Cache Content: %s", memory_cache)

    return {**memory_cache}


@csp_billing_adapter.hookimpl(trylast=True)
def update_cache(config: Config, cache: dict, replace: bool):
    """Update in-memory cache with new content, replacing if specified."""

    global memory_cache

    if replace:
        old_cache = {}
    else:
        old_cache = memory_cache

    memory_cache = {**old_cache, **cache}

    log.info("Updated Cache Content: %s", memory_cache)


@csp_billing_adapter.hookimpl(trylast=True)
def save_cache(config: Config, cache: dict):
    """Save specified content as new in-memory cache contents."""

    update_cache(config, cache, replace=True)
