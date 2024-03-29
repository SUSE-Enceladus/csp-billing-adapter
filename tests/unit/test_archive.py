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

from pytest import mark

from csp_billing_adapter.archive import (
    append_metering_records,
    archive_record
)


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
        archive = append_metering_records(archive, records, 6, 0)

    assert len(archive) == 6
    assert archive[4] == records


def test_append_metering_records_max_bytes():
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

    for i in range(4):
        archive = append_metering_records(archive, records, 6, 456)

    assert len(archive) == 2
    assert archive[0] == records


def test_archive_record(cba_pm, cba_config):
    record = {
        'billing_time': '2024-02-09T18:11:59.527064+00:00',
        'billing_status': {
            'tier_1': {
                'record_id': 'd92c6e6556b14770994f5b64ebe3d339',
                'status': 'succeeded'
            }
        },
        'billed_usage': {
            'tier_1': 10
        },
        'usage_records': [
            {
                'managed_node_count': 9,
                'reporting_time': '2024-01-09T18:11:59.527673+00:00',
                'base_product': 'cpe:/o:suse:product:v1.2.3'
            },
            {
                'managed_node_count': 9,
                'reporting_time': '2024-01-09T18:11:59.529096+00:00',
                'base_product': 'cpe:/o:suse:product:v1.2.3'
            },
            {
                'managed_node_count': 10,
                'reporting_time': '2024-01-09T18:11:59.531424+00:00',
                'base_product': 'cpe:/o:suse:product:v1.2.3'
            }
        ]
    }
    archive_record(
        cba_pm.hook,
        cba_config,
        record
    )
    archive = cba_pm.hook.get_metering_archive(config=cba_config)
    assert len(archive) == 1
    assert archive[0] == record


@mark.config('config_good_average_no_archive.yaml')
def test_archive_disabled(cba_pm, cba_config):
    record = {
        'billing_time': '2024-02-09T18:11:59.527064+00:00',
        'billing_status': {
            'tier_1': {
                'record_id': 'd92c6e6556b14770994f5b64ebe3d339',
                'status': 'succeeded'
            }
        },
        'billed_usage': {
            'tier_1': 10
        },
        'usage_records': [
            {
                'managed_node_count': 9,
                'reporting_time': '2024-01-09T18:11:59.527673+00:00',
                'base_product': 'cpe:/o:suse:product:v1.2.3'
            },
            {
                'managed_node_count': 9,
                'reporting_time': '2024-01-09T18:11:59.529096+00:00',
                'base_product': 'cpe:/o:suse:product:v1.2.3'
            },
            {
                'managed_node_count': 10,
                'reporting_time': '2024-01-09T18:11:59.531424+00:00',
                'base_product': 'cpe:/o:suse:product:v1.2.3'
            }
        ]
    }
    archive_record(
        cba_pm.hook,
        cba_config,
        record
    )
    archive = cba_pm.hook.get_metering_archive(config=cba_config)
    assert len(archive) == 0
