from typing import Callable, Any, Coroutine

from engine.executor.block_call import BlockCall
from engine.executor.variable_reference import VariableRef


class Context:
    recurse: BlockCall
    next: BlockCall
    listen: Callable[[Callable[[str, str], Coroutine]], None]
    broadcast: Callable[[str, str], None]
    set_variable: Callable[[VariableRef, Any], None]
    get_variable: Callable[[VariableRef], Any]
    get_plugin_context: Callable[[str], Any]
