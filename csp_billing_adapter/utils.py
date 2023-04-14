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

import datetime

from dateutil.relativedelta import relativedelta


def get_now():
    return datetime.datetime.now(datetime.timezone.utc)


def date_to_string(date):
    return date.isoformat()


def string_to_date(timestamp):
    return datetime.datetime.fromisoformat(timestamp)


def get_date_delta(date: datetime.datetime, delta: int):
    return date + datetime.timedelta(seconds=delta)


def get_next_bill_time(date: datetime.datetime, billing_interval: str):
    kwargs = {}

    if billing_interval == 'monthly':
        kwargs['months'] = 1
    elif billing_interval == 'hourly':
        kwargs['hours'] = 1

    return date + relativedelta(**kwargs)
