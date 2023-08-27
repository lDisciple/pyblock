from dataclasses import dataclass, field

from engine.blocks.argument import Argument


@dataclass(frozen=True)
class Field(Argument):
    name: str
    type: str = "field_number"


@dataclass(frozen=True)
class Number(Field):
    type: str = "field_number"
    min: int = None
    max: int = None
    precision: int = 1


@dataclass(frozen=True)
class Variable(Field):
    type: str = "field_variable"
    variableTypes: list[str] = None
    variable: str = None


@dataclass(frozen=True)
class Dropdown(Field):
    type: str = "field_dropdown"
    options: list[tuple[str, str]] = field(default_factory=list)
