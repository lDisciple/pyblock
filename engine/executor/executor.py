import builtins
import inspect
import json
import logging
import re
import xml.etree.ElementTree as ElementTree
from typing import Any, Callable, ContextManager, Coroutine

from engine.blocks.block import PyBlockSettings, PyBlockDefinition
from engine.blocks.default import default_blocks
from engine.blocks.fields import Variable
from engine.executor.context import Context
from engine.executor.task import ExecutorStep
from engine.executor.task_loop import ExecutorTaskStack
from engine.executor.value import Value, StatementValue
from engine.executor.variable_reference import VariableRef
from engine.executor.variables.core_variable_handlers import core_variable_handlers
from engine.executor.variables.variable_handler import VariableHandler
from engine.util import anoop

logger = logging.getLogger(__name__)


class ExecutionException(Exception):
    pass


class Executor:
    _namespace_pattern = re.compile(r"xmlns=\"[^\"]+\"")
    starting_blocks: list[ElementTree.Element] = []
    block_definitions: dict[str, PyBlockSettings] = {}
    cached_contexts: dict[str, dict] = {}
    block_factories: dict[str, Callable[[bool], Callable[[Any], Coroutine]]] = {}
    task_stack: ExecutorTaskStack = ExecutorTaskStack()
    variables: dict[VariableRef, Any] = {}
    variable_names: dict[VariableRef, str] = {}
    program: ElementTree.Element
    plugin_contexts: dict[str, Callable[['Executor'], ContextManager]] = {}
    active_contexts: dict[str, ContextManager[Any]] = {}
    event_listeners: [Callable[[str, str], None]] = []
    global_event_listeners: [Callable[[str, str], None]] = []
    variable_handlers: dict[str, VariableHandler] = {}
    stopped: bool

    def __init__(self, load_default_blocks=True):
        self.stopped = False
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
        self.block_factories = {}
        self.cached_contexts = {}

        possible_starting_blocks = set([b["type"] for b in self.block_definitions.values() if b["can_run"]])
        for block in blocks:
            block_type = block.get("type")
            if block_type in possible_starting_blocks:
                self.starting_blocks.append(block)

    def start(self, is_eager=False):
        self.stop()
        self.stopped = False
        self.load_variables()
        self.__create_plugin_contexts()
        self.task_stack = ExecutorTaskStack()
        self.task_stack.run()
        for block in self.starting_blocks:
            logger.debug("Added starting block to task list: %s", block.get("type"))
            self.execute_block(block, is_eager=is_eager)
        self.task_stack.wait_until_complete()
        self.broadcast("executor", "start")

    def step(self):
        self.task_stack.step()

    def complete(self):
        logger.debug("Attempting to run to completion")
        self.task_stack.complete()

    def is_complete(self):
        return len(self.task_stack) == 0 and len(self.event_listeners) == 0

    def stop(self):
        self.task_stack.stop()
        self.event_listeners.clear()
        self.stopped = True
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

    def execute_block(self, block_node: ElementTree.Element, is_eager=True) -> Any:
        block_factory = self.get_block_function_factory(block_node)
        self.task_stack.add_task(block_factory(is_eager)())

    def get_block_function_factory(self, block_node: ElementTree.Element):

        block_id = block_node.get("id")
        if block_id in self.block_factories:
            return self.block_factories[block_id]

        block_type = block_node.get("type")
        block_settings = self.get_block_settings(block_type)
        block_definition = block_settings["definition"]
        block_is_run_type = block_settings["can_run"]

        default_func_kwargs: dict[str, Any | Context] = self.extract_context(block_node, block_definition)
        default_func_kwargs = {Executor.remove_reserved_words_from_param_name(k): v for k, v in
                               default_func_kwargs.items()}

        def block_task_create(is_eager: bool):
            if self.stopped:
                return anoop

            async def block_task(**kwargs):
                logger.debug(
                    f"TEST block '{block_type}' {'eagerly ' if is_eager else ''}with context:")
                await ExecutorStep(block_id, block_type, is_eager or block_is_run_type)
                func_kwargs = {**default_func_kwargs, **kwargs}
                func_kwargs.update(self.create_default_context(block_node, is_eager))
                await Executor.__resolve_block_task_value_kwargs(block_settings, func_kwargs, is_eager)
                logger.debug(
                    f"Executing block '{block_type}' {'eagerly ' if is_eager else ''}with context: {func_kwargs}")
                try:
                    return_value = block_settings["func"](**func_kwargs)
                    if inspect.isawaitable(return_value):
                        return_value = await return_value
                except Exception as e:
                    logger.error("Could not execute block", exc_info=e)
                    self.broadcast_exception(e)
                    return None
                logger.debug(f"Executed block '{block_type}' returned '{return_value}' using context: {func_kwargs}")
                return return_value
            return block_task

        self.block_factories[block_id] = block_task_create
        return block_task_create

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

    def extract_context_with_cache(self, current_block: ElementTree.Element, block_definition: PyBlockDefinition):
        block_id = current_block.get("id")
        if block_id is None:
            return self.extract_context(current_block, block_definition)
        cache_key = block_id
        if cache_key in self.cached_contexts:
            return self.cached_contexts[cache_key]
        context = self.extract_context(current_block, block_definition)
        self.cached_contexts[cache_key] = context
        return context

    def extract_context(self, current_block: ElementTree.Element, block_definition: PyBlockDefinition):
        context = self.__get_block_kwargs_defaults(block_definition)
        for el in current_block:
            name = el.get("name").lower() if el.get("name") else None
            is_ref_type = self.__is_variable_ref_type(current_block, name)
            if el.tag == "field":
                context[name] = self.parse_field(el, is_ref_type)
            elif el.tag == "value":
                context[name] = self.parse_value(el, is_ref_type)
            elif el.tag == "statement":
                context[name] = self.parse_statement(el)
        return context

    def create_default_context(self, block: ElementTree.Element, is_eager=True):
        next_block = block.find("next")

        context_obj = Context()
        context_obj.recurse = self.get_block_function_factory(block)(is_eager)
        context_obj.next = self.get_block_function_factory(next_block.find("block"))(is_eager) if next_block else anoop
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
            return Value(lambda: self.get_variable(var_ref))
        else:
            field_type = el.get("name")
            if field_type == "NUM":
                return float(el.text)
            return el.text or ""

    def parse_value(self, el: ElementTree.Element, is_ref_type=False):
        block = el.find("block")
        if block is not None:
            return Value(self.get_block_function_factory(block)(True))
        shadow = el.find("shadow")
        if shadow is not None:
            return self.parse_shadow(shadow, is_ref_type)
        raise ExecutionException("Could not parse value block")

    def parse_shadow(self, el, is_ref_type=False):
        field = el.find("field")
        if field is not None:
            return self.parse_field(field, is_ref_type)
        raise ExecutionException("Could not parse shadow block. No field element found")

    def parse_statement(self, el: ElementTree.Element) -> Value[Callable]:
        block = el.find("block")
        if block is not None:
            return StatementValue(self.get_block_function_factory(block))
        return Value(lambda: anoop)

    def add_broadcast_listener(self, callback: Callable[[str, str], Coroutine | None]):
        self.event_listeners.append(callback)

    """
    Adds an event listener that does not get removed on every run
    """

    def add_global_broadcast_listener(self, callback: Callable[[str, str], None]):
        self.global_event_listeners.append(callback)

    def broadcast(self, topic: str, message: str):
        for event_listener in self.global_event_listeners + self.event_listeners:
            try:
                response = event_listener(topic, message)
                if response is not None:
                    self.task_stack.add_task(response)
            except Exception as e:
                logger.error("Failed to run from broadcast", exc_info=e)
                self.broadcast_exception(e)

    def broadcast_exception(self, e: Exception):
        self.broadcast("error", f"{type(e).__name__}: {str(e)}")

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
        return self.task_stack.get_highlights()

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

    @staticmethod
    def __is_value_immediate(block_settings: PyBlockSettings, name: str):
        if name is None:
            return True

        # Check annotations
        func: Any = block_settings["func"]
        type_hints = func.__annotations__
        sanitised_name = Executor.remove_reserved_words_from_param_name(name)
        if type_hints is not None and sanitised_name in type_hints and type_hints[sanitised_name] == Value:
            return False

        # Default to immediate-type
        return True

    @staticmethod
    async def __resolve_block_task_value_kwargs(block_settings: PyBlockSettings, func_kwargs: dict, is_eager: bool):
        for k in func_kwargs:
            if issubclass(type(func_kwargs[k]), Value) and Executor.__is_value_immediate(block_settings, k):
                if type(func_kwargs[k]) == StatementValue:
                    func_kwargs[k] = func_kwargs[k].get(is_eager)
                else:
                    func_kwargs[k] = await func_kwargs[k].get()

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

    @staticmethod
    def __get_block_kwargs_defaults(block_definition: PyBlockDefinition):
        func_kwargs = {}
        if block_definition and block_definition.arguments is not None:
            for arg in block_definition.arguments:
                func_kwargs[arg.name.lower()] = arg.get_default()
        return func_kwargs
