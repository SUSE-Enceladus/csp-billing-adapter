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


def append_metering_records(
    archive: list,
    billing_record: dict,
    max_length: int
) -> list:
    """
    Append usage and metering records to the archive

    If archive is larger than max length, drop the oldest record.

    :param archive:
        The list of meterings and usage records to append to.
    :param billing_record:
        The dictionary containing the most recent
        metering and usage records to be archived.
    :param max_length:
        The max size of the archive list.
    :return:
        The archive of meterings and usage records with the
        billing_record appended. If archive ends up greater
        than max lengh the first (oldest) record is dropped.
    """
    archive.append(billing_record)

    if len(archive) > max_length:
        return archive[1:]
    else:
        return archive
