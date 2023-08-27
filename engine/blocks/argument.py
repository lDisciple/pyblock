from abc import ABC


class Argument(ABC):
    name: str

    def get_default(self):
        return None

    def get_dict(self):
        return {k: v for k, v in self.__dict__.items() if v is not None}
