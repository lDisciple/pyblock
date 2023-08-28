import inspect
import logging
import re
import sys
from collections import deque
from dataclasses import dataclass, field
from typing import Unpack, TypedDict, NotRequired, Optional, Callable

from engine.blocks.argument import Argument
from engine.blocks.output_shapes import OutputShape
from engine.util import noop

logger = logging.getLogger(__name__)


@dataclass()
class PyBlockDefinition:
    title: str = "Unknown Block"
    color: int = 160
    arguments: list[Argument] = field(default_factory=list)
    has_next_statement: bool = False  # Could add a statement type field
    has_previous_statement: bool = False  # Could add a statement type
    output: str = None
    output_shape: Optional[OutputShape] = None
    extensions: list[str] = None


class PyBlockSettings(TypedDict, total=False):
    category: NotRequired[Optional[str]]
    type: Optional[str]
    is_visible: bool
    can_run: bool
    is_predefined: bool
    func: Callable
    definition: Optional[PyBlockDefinition]


class ManagedPyBlockSettings(TypedDict, PyBlockSettings, total=False):
    _pyblock: bool


default_settings = ManagedPyBlockSettings(
    _pyblock=True,
    category=None,
    type=None,
    is_visible=True,
    can_run=False,
    is_predefined=False,
    func=noop,
    definition=None
)

__loaded_blocks: dict[str, PyBlockSettings] = {}


def pyblock(**kwargs: Unpack[PyBlockSettings]):
    settings: ManagedPyBlockSettings = ManagedPyBlockSettings()
    settings.update(default_settings)
    settings.update(kwargs)

    def decorator(func: Callable) -> ManagedPyBlockSettings:
        settings["func"] = func
        settings["type"] = func.__name__
        logger.debug(f"Loaded PyBlock '{func.__name__}'")
        __loaded_blocks[func.__name__] = settings
        return settings

    return decorator


def get_all_imported_blocks() -> dict[str, PyBlockSettings]:
    return __loaded_blocks


def get_block_definition(block: PyBlockSettings):
    if block["is_predefined"] or block["definition"] is None:
        return None

    definition = block["definition"]
    block_type = block["type"]

    result = {
        "colour": definition.color
    }
    arguments_queue = deque(definition.arguments)
    for i, message in enumerate(definition.title.split("\n")):
        result[f"args{i}"] = []
        message_arg_counter = 0

        def sub(m: re.Match):
            nonlocal message_arg_counter
            message_arg_counter = message_arg_counter + 1
            try:
                result[f"args{i}"].append(arguments_queue.popleft())
            except IndexError:
                raise IndexError(f"Too few arguments found for block '{block_type}'")
            return f"%{message_arg_counter}"
        result[f"message{i}"] = re.sub(r"%\d+", sub, message)

    if definition.has_previous_statement:
        result["previousStatement"] = None
    if definition.has_next_statement:
        result["nextStatement"] = None
    if definition.output_shape:
        result["outputShape"] = definition.output_shape.value
    if definition.output:
        result["output"] = definition.output
    if definition.extensions:
        result["extensions"] = definition.extensions
    return result


def collect_blocks(module_name: str) -> list[PyBlockSettings]:
    blocks = inspect.getmembers(sys.modules[module_name], lambda x: type(x) == dict and "_pyblock" in x)
    return [b[1] for b in blocks]
