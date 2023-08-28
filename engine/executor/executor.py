import builtins
import json
import logging
import re
import xml.etree.ElementTree as ElementTree
from collections import deque
from typing import Any, Callable, ContextManager

from engine.blocks.block import PyBlockSettings, PyBlockDefinition
from engine.blocks.default import default_blocks
from engine.blocks.fields import Variable
from engine.executor.context import Context
from engine.executor.variable_reference import VariableRef
from engine.executor.variables.core_variable_handlers import core_variable_handlers
from engine.executor.variables.variable_handler import VariableHandler
from engine.util import noop

logger = logging.getLogger(__name__)


class ExecutionException(Exception):
    pass


class ExecutorTask:
    element: ElementTree.Element
    extra_kwargs: dict

    def __init__(self, element: ElementTree, **kwargs):
        self.element = element
        self.extra_kwargs = kwargs


class Executor:
    _namespace_pattern = re.compile(r"xmlns=\"[^\"]+\"")
    starting_blocks: list[ElementTree.Element] = []
    block_definitions: dict[str, PyBlockSettings] = {}
    task_stack: deque[ExecutorTask] = deque()
    variables: dict[VariableRef, Any] = {}
    variable_names: dict[VariableRef, str] = {}
    program: ElementTree.Element
    plugin_contexts: dict[str, Callable[['Executor'], ContextManager]] = {}
    active_contexts: dict[str, ContextManager[Any]] = {}
    event_listeners: [Callable[[str, str], None]] = []
    global_event_listeners: [Callable[[str, str], None]] = []
    variable_handlers: dict[str, VariableHandler] = {}

    def __init__(self, load_default_blocks=True):
        if load_default_blocks:
            self.load_blocks(default_blocks)
        for handler in core_variable_handlers:
            self.add_variable_handler(handler())

    def load_blocks(self, blocks: list[PyBlockSettings]):
        for block in blocks:
            self.block_definitions[block["type"]] = block

    def load_program(self, xml_string: str):
        xml_string = self._namespace_pattern.sub("", xml_string)
        self.program = ElementTree.fromstring(xml_string)
        blocks = self.program.findall("block")
        self.stop()
        self.starting_blocks = []

        possible_starting_blocks = set([b["type"] for b in self.block_definitions.values() if b["can_run"]])
        for block in blocks:
            block_type = block.get("type")
            if block_type in possible_starting_blocks:
                self.starting_blocks.append(block)

    def start(self, is_eager=False):
        self.stop()
        self.load_variables()
        self.__create_plugin_contexts()
        for block in self.starting_blocks:
            logger.debug("Added starting block to task list: %s", block.get("type"))
            self.execute_block(block, is_eager=is_eager)
        self.broadcast("executor", "start")

    def step(self):
        if not len(self.task_stack):
            return
        current_block = self.task_stack.popleft()
        self.execute_task(current_block, is_eager=False)

    def complete(self):
        logger.debug("Attempting to run to completion")
        while len(self.task_stack) > 0:
            current_block = self.task_stack.popleft()
            self.execute_task(current_block, is_eager=True)

    def is_complete(self):
        return len(self.task_stack) == 0 and len(self.event_listeners) == 0

    def stop(self):
        self.task_stack.clear()
        self.event_listeners.clear()
        self.__close_plugin_contexts()

    def get_variables_json(self):
        return json.dumps({f"{ref[0]}-{ref[1]}": v for ref, v in self.variables.items()})

    def get_variables(self):
        return [{
            "value": value,
            "type": ref[0],
            "id": ref[1],
            "name": self.variable_names[ref]
        } for ref, value in self.variables.items()]

    def execute_block(self, block: ElementTree.Element, is_eager=True) -> Any:
        return self.execute_task(ExecutorTask(block), is_eager=is_eager)

    def execute_task(self, task: ExecutorTask, is_eager=True) -> Any:
        block_node = task.element
        block_type = block_node.get("type")
        block_settings = self.get_block_settings(block_type)
        block_definition = block_settings["definition"]

        func_kwargs: dict[str, Context] = self.extract_context(block_node, is_eager=is_eager)
        func_kwargs = {Executor.remove_reserved_words_from_param_name(k): v for k, v in func_kwargs.items()}
        func_kwargs.update(task.extra_kwargs)
        if block_definition:
            for arg in block_definition.arguments:
                if arg.name.lower() not in func_kwargs:
                    func_kwargs[arg.name.lower()] = arg.get_default()

        logger.debug(f"Executing block '{block_type}' {'eagerly ' if is_eager else ''}with context: {func_kwargs}")
        return_value = block_settings["func"](**func_kwargs)
        logger.debug(f"Executed block '{block_type}' returned '{return_value}' using context: {func_kwargs}")
        return return_value

    def load_variables(self):
        variables = self.program.find("variables")
        if not variables:
            return
        for variable in variables:
            var_id: str = variable.get("id")
            var_type: str = variable.get("type")
            var_name: str = variable.text
            var_ref = VariableRef(var_type, var_id)
            if var_type in self.variable_handlers:
                self.variables[var_ref] = self.variable_handlers[var_type].get_default_value(variable)
            else:
                self.variables[var_ref] = variable.text
            self.variable_names[var_ref] = var_name
            logger.debug(f"Loaded variable: [{var_ref[0]}-{var_ref[1]}]={self.variables[var_ref]}")

    def extract_context(self, current_block: ElementTree.Element, is_eager=True):
        context = self.create_default_context(current_block, is_eager=is_eager)
        for el in current_block:
            name = el.get("name").lower() if el.get("name") else None
            is_ref_type = self.__is_variable_ref_type(current_block, name)
            if el.tag == "field":
                context[name] = self.parse_field(el, is_ref_type)
            elif el.tag == "value":
                context[name] = self.parse_value(el, is_ref_type)
            elif el.tag == "statement":
                context[name] = self.parse_statement(el, is_eager)
        return context

    def create_default_context(self, block: ElementTree.Element, is_eager=True):
        next_block = block.find("next")

        context_obj = Context()
        context_obj.recurse = self.create_callable_block(block, is_eager)
        context_obj.next = self.create_callable_block(next_block.find("block"), is_eager) if next_block else noop
        context_obj.listen = self.add_broadcast_listener
        context_obj.broadcast = self.broadcast
        context_obj.set_variable = self.set_variable
        context_obj.get_variable = self.get_variable
        context_obj.get_plugin_context = lambda k: self.active_contexts[k]

        return {
            "context": context_obj
        }

    def parse_field(self, el, is_ref_type):
        var_id: str = el.get("id")
        if var_id is not None:
            var_type: str = el.get("variabletype")
            var_ref = VariableRef(var_type, var_id)
            if is_ref_type:
                return var_ref
            return self.get_variable(var_ref)
        else:
            field_type = el.get("name")
            if field_type == "NUM":
                return float(el.text)
            return el.text

    def parse_value(self, el: ElementTree.Element, is_ref_type = False):
        block = el.find("block")
        if block is not None:
            return self.execute_block(block, is_eager=True)
        shadow = el.find("shadow")
        if shadow is not None:
            return self.parse_shadow(shadow, is_ref_type)
        raise ExecutionException("Could not parse value block")

    def parse_statement(self, el: ElementTree.Element, is_eager: bool) -> Callable:
        block = el.find("block")
        if block is not None:
            return self.create_callable_block(block, is_eager)
        return noop

    def create_callable_block(self, block: ElementTree.Element, is_eager_call: bool) -> Callable:
        def func(is_eager=is_eager_call, **kwargs):
            task = ExecutorTask(block, **kwargs)
            if is_eager:
                return self.execute_task(task, is_eager=is_eager)
            else:
                return self.task_stack.append(task)

        return func

    def parse_shadow(self, el, is_ref_type = False):
        field = el.find("field")
        if field is not None:
            return self.parse_field(field, is_ref_type)
        raise ExecutionException("Could not parse shadow block. No field element found")

    def add_broadcast_listener(self, callback: Callable[[str, str], None]):
        self.event_listeners.append(callback)

    """
    Adds an event listener that does not get removed on every run
    """
    def add_global_broadcast_listener(self, callback: Callable[[str, str], None]):
        self.global_event_listeners.append(callback)

    def broadcast(self, topic: str, message: str):
        for event_listener in self.global_event_listeners:
            event_listener(topic, message)
        for event_listener in self.event_listeners:
            event_listener(topic, message)

    def set_variable(self, ref: VariableRef, value: Any):
        if logger.level <= logging.DEBUG:
            old_value = self.variables[ref] if ref in self.variables else None
            logger.debug(f"Updated variable '{ref[0]}-{ref[1]}': {old_value} -> {value}")
        self.broadcast("variable", "change")
        self.variables[ref] = value

    def get_variable(self, ref: VariableRef):
        return self.variables[ref]

    def get_variable_names(self):
        return self.variable_names

    def get_block_settings(self, block_type):
        try:
            return self.block_definitions[block_type]
        except KeyError as e:
            raise ExecutionException(f"Unknown block type {e}")

    def get_highlights(self):
        return [self.task_stack[0].element.get("id")] if len(self.task_stack) > 0 else []

    def get_task_count(self):
        return len(self.task_stack)

    @staticmethod
    def remove_reserved_words_from_param_name(name: str):
        if name in globals() or name in dir(builtins):
            return f"param_{name}"
        return name

    def add_variable_handler(self, handler: VariableHandler):
        self.variable_handlers[handler.get_type_name()] = handler

    def add_plugin_context(self, context_creator: Callable[[], ContextManager]):
        key = context_creator.__name__
        self.plugin_contexts[key] = context_creator

    def __is_variable_ref_type(self, block_node: ElementTree.Element, name: str):
        if name is None:
            return False

        block_type = block_node.get("type")
        block_settings = self.get_block_settings(block_type)
        # Check arguments first
        if "definition" in block_settings and block_settings["definition"] is not None:
            definition: PyBlockDefinition = block_settings["definition"]
            for arg in definition.arguments:
                if arg.name == name:
                    return type(arg) == Variable
        # Check annotations
        func: Any = block_settings["func"]
        type_hints = func.__annotations__
        sanitised_name = Executor.remove_reserved_words_from_param_name(name)
        if type_hints is not None and sanitised_name in type_hints and type_hints[sanitised_name] == VariableRef:
            return True

        # Default to value-type
        return False


    def __create_plugin_contexts(self):
        for key, plugin_context_creator in self.plugin_contexts.items():
            context = plugin_context_creator(self)
            context.__enter__()
            self.active_contexts[key] = context

    def __close_plugin_contexts(self):
        for plugin_context in self.active_contexts.values():
            if plugin_context.__exit__:
                plugin_context.__exit__(None, None, None)
        self.active_contexts.clear()
