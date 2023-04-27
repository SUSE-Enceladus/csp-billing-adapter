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

"""Pluggy hook interface specifications for CSP interactions."""

import pluggy

from csp_billing_adapter.config import Config

hookspec = pluggy.HookspecMarker('csp_billing_adapter')


@hookspec(firstresult=True)
def meter_billing(
    config: Config,
    dimensions: dict,
    timestamp: str,
) -> str:
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
) -> None:
    """
    Retrieve billing data from CSP API within between start and end time

    :param config: The application configuration dictionary
    :param start_time: Timestamp for the lower search bound
    :param end_time: Timestamp for the upper search bound
    """


@hookspec(firstresult=True)
def get_csp_name(config: Config) -> str:
    """
    Retrieves the CSP name from the loaded plugin

    :param config: The application configuration dictionary
    :return: Returns the CSP name
    """


@hookspec(firstresult=True)
def get_account_info(config: Config) -> dict:
    """
    Retrieves the account information from the loaded plugin

    :param config: The application configuration dictionary
    :return: Returns a dictionary of the account info from CSP
    """
