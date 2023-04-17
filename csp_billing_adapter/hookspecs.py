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
def get_usage_data(config: Config):
    """
    Retrieves the current usage report from API

    :param config: The application configuration dictionary
    :return: Return a hash with the current usage report
    """


@hookspec(firstresult=True)
def load_defaults(defaults: dict):
    pass
