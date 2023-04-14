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

import yaml


class Config:
    def __init__(self, data: dict):
        for key, val in data.items():
            if isinstance(val, (list, tuple, set)):
                attr = []
                for item in val:
                    attr.append(self.parse_value(item))

                setattr(self, key, attr)
            else:
                setattr(self, key, self.parse_value(val))

    @staticmethod
    def parse_value(item):
        return Config(item) if isinstance(item, dict) else item

    @staticmethod
    def load_defaults(data, hook):
        defaults = {}
        hook.load_defaults(defaults=defaults)
        return {**defaults, **data}

    @classmethod
    def load_from_file(cls, filename, hook):
        with open(filename, 'r') as fh:
            yaml_data = yaml.safe_load(fh)

        data = cls.load_defaults(yaml_data, hook)

        return cls(data)

    def __repr__(self):
        return '{%s}' % str(
            ', '.join(
                f"'{key}': {repr(val)}" for key, val in self.__dict__.items()
            )
        )
