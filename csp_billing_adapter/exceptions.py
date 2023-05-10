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

"""CSP Billing Adapater specific exceptions."""


class CSPBillingAdapterException(Exception):
    """Base exception class for CSP Billing Adapter exceptions."""


class NoMatchingVolumeDimensionError(CSPBillingAdapterException):
    """
    Exception raised when no matching volume dimension is found for
    a metric's value in the config's usage_metrics settings.

    Attributes:
        metric -- the name of the metric
        value -- the value of the metric
    """

    def __init__(self, metric, value):
        self.metric = metric
        self.value = value
        self.msg = (
            'No matching volume dimension found for '
            f'{self.metric!r}={self.value}'
        )

    def __str__(self):
        return self.msg


class FailedToSaveCSPConfigError(CSPBillingAdapterException):
    """Exception raised when csp_config save/update fails."""


class FailedToSaveCacheError(CSPBillingAdapterException):
    """Exception raised when cache save/update fails."""
