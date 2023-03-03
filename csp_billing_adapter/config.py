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
