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

"""Utility functions for handling a rolling dictionary archive."""

import functools
import logging
import json

from csp_billing_adapter.config import Config
from csp_billing_adapter.utils import retry_on_exception

log = logging.getLogger('CSPBillingAdapter')

DEFAULT_RETENTION_PERIOD = 6  # in months
DEFAULT_BYTES_LIMIT = 0


def append_metering_records(
    archive: list,
    billing_record: dict,
    max_length: int,
    max_bytes: int
) -> list:
    """
    Append usage and metering records to the archive

    If archive is larger than max length drop the oldest
    record. If the archive is larger than the max bytes
    limit trim it until it satisfies the limit.

    :param archive:
        The list of meterings and usage records to append to.
    :param billing_record:
        The dictionary containing the most recent
        metering and usage records to be archived.
    :param max_length:
        The max size of the archive list.
    :param max_bytes:
        The max size in bytes of the archive.
    :return:
        The archive of meterings and usage records with the
        billing_record appended. If archive ends up greater
        than max lengh or max bytes the archive is trimmed
        as necessary to satisfy both max_length and
        max_bytes.
    """
    archive.append(billing_record)

    if len(archive) > max_length:
        archive = archive[1:]

    if max_bytes > 1:
        # Treat 0 and 1 the same. Disable max bytes option.
        # This prevents infitite loop when value is 1 since
        # empty list is 2 bytes.
        while True:
            # Trim archive until it is smaller than max bytes
            archive_size = len(bytes(json.dumps(archive), 'utf-8'))

            if archive_size > max_bytes:
                archive = archive[1:]
            else:
                break

    return archive


def archive_record(
    hook,
    config: Config,
    billing_record: dict
) -> None:
    """
    :param hook:
        The Pluggy plugin manager hook that will be
        used to call the meter_billing operation.
    :param config:
        The configuration specifying the metrics that
        need to be processed in the usage records list.
    :param billing_record:
        The dictionary containing the most recent
        metering and usage records to be archived.
    """
    archive = retry_on_exception(
        functools.partial(
            hook.get_metering_archive,
            config=config,
        ),
        logger=log,
        func_name="hook.get_metering_archive"
    )

    if archive is None:
        archive = []

    archive = append_metering_records(
        archive,
        billing_record,
        config.archive_retention_period or DEFAULT_RETENTION_PERIOD,
        config.archive_bytes_limit or DEFAULT_BYTES_LIMIT
    )

    retry_on_exception(
        functools.partial(
            hook.save_metering_archive,
            config=config,
            archive_data=archive
        ),
        logger=log,
        func_name="hook.save_metering_archive"
    )
