from dataclasses import dataclass

from engine.blocks.argument import Argument
from engine.util import noop


@dataclass(frozen=True)
class Input(Argument):
    name: str
    type: str = "input_value"


@dataclass(frozen=True)
class InputValue(Input):
    type: str = "input_value"

    def get_default(self):
        return ""


@dataclass(frozen=True)
class InputStatement(Input):
    type: str = "input_statement"

    def get_default(self):
        return noop


@dataclass(frozen=True)
class InputDummy(Input):
    type: str = "input_dummy"
