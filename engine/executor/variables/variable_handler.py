from abc import ABC, abstractmethod
from typing import Any
from xml.etree import ElementTree


class VariableHandler(ABC):
    @abstractmethod
    def get_default_value(self, variable: ElementTree.Element) -> Any:
        pass

    @abstractmethod
    def get_type_name(self) -> str:
        pass
