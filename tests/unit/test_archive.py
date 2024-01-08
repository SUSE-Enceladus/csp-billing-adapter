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
test_archive is part of csp-billing-adapter and provides units tests
for the archive util functions.
"""

from csp_billing_adapter.archive import append_metering_records


def test_append_metering_records():
    archive = []
    records = {
        "bill_time": "2024-01-03T20:06:42.076972+00:00",
        "metering_id": "FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF",
        "usage_records": [
            {
                "managed_node_count": 9,
                "managed_systems": 6,
                "reporting_time": "2024-01-03T20:06:42.076972+00:00"
            }
        ]
    }

    for i in range(10):
        archive = append_metering_records(archive, records, 6)

    assert len(archive) == 6
    assert archive[4] == records
