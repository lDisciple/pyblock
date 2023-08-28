from xml.etree import ElementTree

from engine.executor.variables.variable_handler import VariableHandler


class PlainVariableHandler(VariableHandler):
    def get_type_name(self):
        return ""

    def get_default_value(self, variable: ElementTree.Element):
        return 0


class BroadcastVariableHandler(VariableHandler):
    def get_type_name(self):
        return "broadcast_msg"

    def get_default_value(self, variable: ElementTree.Element):
        return variable.text


class ListVariableHandler(VariableHandler):
    def get_type_name(self):
        return "list"

    def get_default_value(self, variable: ElementTree.Element):
        return []


core_variable_handlers = [PlainVariableHandler, BroadcastVariableHandler, ListVariableHandler]