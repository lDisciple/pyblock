from typing import Any

from engine.blocks.block import pyblock, collect_blocks
from engine.executor.context import Context, VariableRef


@pyblock(category="data", is_predefined=True)
def data_setvariableto(context: Context, variable: VariableRef, value: Any):
    context.set_variable(variable, value)
    context.next()


@pyblock(category="data", is_predefined=True)
def data_changevariableby(context: Context, variable: VariableRef, value: Any):
    context.set_variable(variable, context.get_variable(variable) + int(value))
    context.next()


@pyblock(category="data", is_predefined=True)
def data_variable(context: Context, variable: VariableRef):
    return context.get_variable(variable)


@pyblock(category="data", is_predefined=True)
def data_showvariable(context: Context, variable: VariableRef):
    context.next()


@pyblock(category="data", is_predefined=True)
def data_hidevariable(context: Context, variable: VariableRef):
    context.next()


@pyblock(category="data", is_predefined=True)
def data_addtolist(context: Context, param_list: VariableRef, item: Any):
    var_value = context.get_variable(param_list)
    if type(var_value) != list:
        var_value = list(var_value)
    var_value.append(item)
    context.set_variable(param_list, var_value)
    context.next()


@pyblock(category="data", is_predefined=True)
def data_insertatlist(context: Context, param_list: VariableRef, item: Any, index: int):
    var_value = context.get_variable(param_list)
    if type(var_value) != list:
        var_value = list(var_value)
    var_value.insert(int(index), item)
    context.set_variable(param_list, var_value)
    context.next()


@pyblock(category="data", is_predefined=True)
def data_deleteoflist(context: Context, param_list: VariableRef, index: int):
    var_value = context.get_variable(param_list)
    if type(var_value) != list:
        var_value = list(var_value)
    index = int(index)
    var_value = var_value[:index] + var_value[index + 1:]
    context.set_variable(param_list, var_value)
    context.next()


@pyblock(category="data", is_predefined=True)
def data_deletealloflist(context: Context, param_list: VariableRef):
    context.set_variable(param_list, [])
    context.next()


@pyblock(category="data", is_predefined=True)
def data_showlist(context: Context, param_list: VariableRef):
    context.next()


@pyblock(category="data", is_predefined=True)
def data_hidelist(context: Context, param_list: VariableRef):
    context.next()


data_blocks = collect_blocks(__name__)
