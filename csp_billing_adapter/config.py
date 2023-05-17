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
"""config.py is part of csp-billing-adapter and defines the Config class"""

import logging
import yaml
from yaml.parser import ParserError

log = logging.getLogger('CSPBillingAdapter')


class Config(dict):
    """
    The Config class handles reading configuartion settings
    from a provided configuration file and loading default settings from
    any configured plugins  This class is based on a dict to allow access
    using both dot notation and key lookup.

    For example:

        result = Config(config_data)
        print(result.get('Name'))
        print(result.Name)

    """

    def __init__(self, data: dict):
        super().__init__(data)
        for key, val in data.items():
            if isinstance(val, (list, tuple, set)):
                log.debug(
                    "Converting collection %s to: %s",
                    repr(val),
                    self.__class__.__name__
                )
                attr = [self.parse_value(item) for item in val]
                setattr(self, key, attr)
            else:
                setattr(self, key, self.parse_value(val))

        log.debug("Config: %s", self)

    def parse_value(self, item):
        """recursive evaluation if item is a dict"""
        if isinstance(item, dict):
            log.debug(
                "Converting dict %s to: %s",
                item,
                self.__class__.__name__
            )
            parsed_item = self.__class__(item)
        else:
            log.debug("Using original item: %s", item)
            parsed_item = item

        log.debug("Parsed item: %s", parsed_item)

        return parsed_item

    @staticmethod
    def load_defaults(data, hook):
        """
        Merge provided config data over any plugin provided default settings.

        Args:
            data (dict): A dict of the current settings
            hook (configured hook):

        Returns:
            [dict]: A dictionary containing all of the configuration settings
        """

        defaults = {}
        hook.load_defaults(defaults=defaults)

        log.debug("Config defaults loaded: %s", defaults)

        updated_data = {**defaults, **data}

        log.debug("Merged config with defaults: %s", updated_data)

        return updated_data

    @classmethod
    def load_from_file(cls, filename, hook):
        """
        Load settings/values from the specified YAML configuration file,
        merging appropriately with any defaults that registered plugins may
        provide.

        Args:
            filename (filepath): The path to csp-billing-adapter
            configuration file.
            hook (configured hook):

        Returns:
            [Config]: A instance of Config containing all of the configuration
            settings.
        """

        try:
            with open(filename, 'r', encoding='utf-8') as fh:
                yaml_data = yaml.safe_load(fh)
        except (FileNotFoundError, ParserError) as exc:
            raise exc
        log.debug(
            "Loaded YAML %s as: %s",
            filename,
            yaml_data
        )
        data = cls.load_defaults(yaml_data, hook)
        return cls(data)
