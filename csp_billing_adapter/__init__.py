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

"""
csp-billing-adapter

This package provides the core implementation of the Cloud Service
Provider (CSP) Billing Adapter.

This core implementation is intended to be CSP and deployment
framework agnostic, providing Pluggy hook interface specifications
that allow plugins to be registered that provide CSP or deployment
framework specific implementations of required functionality.
"""

import pluggy

__author__ = """SUSE"""
__email__ = 'public-cloud-dev@susecloud.net'
__version__ = '0.10.0'

hookimpl = pluggy.HookimplMarker('csp_billing_adapter')
"""Marker to be imported and used in plugins (and for own implementations)"""
