#
# Copyright 2024 SUSE LLC
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

"""
Pluggy hook interface specifications for archival storage related functionality
"""

import pluggy

from csp_billing_adapter.config import Config

hookspec = pluggy.HookspecMarker('csp_billing_adapter')


@hookspec(firstresult=True)
def get_archive_location() -> str:
    """
    Returns the location of the archive data storage
    """


@hookspec(firstresult=True)
def get_metering_archive(config: Config) -> list:
    """
    Retrieves the archive data from stateful storage

    :param config: The application configuration dictionary
    :return: Return a list of the archive data which contains a history
             of recent meterings. The length of this data is determined
             by application config.
    """


@hookspec(firstresult=True)
def save_metering_archive(config: Config, archive_data: list) -> None:
    """
    Saves the metering archive data to stateful storage

    :param config: The application configuration dictionary
    :param archive_data: A list of metering archive data
    """
