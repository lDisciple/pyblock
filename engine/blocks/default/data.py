from typing import Any

from engine.blocks.block import pyblock, collect_blocks
from engine.executor.context import Context, VariableRef


def __get_variable_list(context: Context, variable_ref: VariableRef):
    var_value = context.get_variable(variable_ref)
    if type(var_value) != list:
        var_value = list(var_value)
    return var_value


@pyblock(category="data", is_predefined=True)
async def data_setvariableto(context: Context, variable: VariableRef, value: Any):
    context.set_variable(variable, value)
    await context.next()


@pyblock(category="data", is_predefined=True)
async def data_changevariableby(context: Context, variable: VariableRef, value: Any):
    context.set_variable(variable, float(context.get_variable(variable)) + float(value))
    await context.next()


@pyblock(category="data", is_predefined=True)
def data_variable(context: Context, variable: VariableRef):
    return context.get_variable(variable)


@pyblock(category="data", is_predefined=True)
async def data_showvariable(context: Context, variable: VariableRef):
    await context.next()


@pyblock(category="data", is_predefined=True)
async def data_hidevariable(context: Context, variable: VariableRef):
    await context.next()


@pyblock(category="data", is_predefined=True)
async def data_addtolist(context: Context, param_list: VariableRef, item: Any):
    var_value = __get_variable_list(context, param_list)
    var_value.append(item)
    context.set_variable(param_list, var_value)
    await context.next()


@pyblock(category="data", is_predefined=True)
async def data_insertatlist(context: Context, param_list: VariableRef, item: Any, index: int):
    var_value = __get_variable_list(context, param_list)
    var_value.insert(int(index), item)
    context.set_variable(param_list, var_value)
    await context.next()


@pyblock(category="data", is_predefined=True)
async def data_deleteoflist(context: Context, param_list: VariableRef, index: int):
    var_value = __get_variable_list(context, param_list)
    index = int(index)
    var_value = var_value[:index] + var_value[index + 1:]
    context.set_variable(param_list, var_value)
    await context.next()


@pyblock(category="data", is_predefined=True)
async def data_replaceitemoflist(context: Context, param_list: VariableRef, index: int, item: Any):
    var_value = __get_variable_list(context, param_list)
    index = int(index)
    var_value = var_value[:index] + [item] + var_value[index + 1:]
    context.set_variable(param_list, var_value)
    await context.next()


@pyblock(category="data", is_predefined=True)
async def data_itemoflist(context: Context, param_list: VariableRef, index: int):
    var_value = __get_variable_list(context, param_list)
    index = int(index)
    return var_value[index]


@pyblock(category="data", is_predefined=True)
def data_itemnumoflist(context: Context, param_list: VariableRef, item: Any):
    var_value = __get_variable_list(context, param_list)

    for i, el in enumerate(var_value):
        if el == item:
            return i
    return -1


@pyblock(category="data", is_predefined=True)
def data_lengthoflist(context: Context, param_list: VariableRef):
    var_value = __get_variable_list(context, param_list)
    return len(var_value)


@pyblock(category="data", is_predefined=True)
def data_listcontents(context: Context, param_list: VariableRef):
    var_value = __get_variable_list(context, param_list)
    return var_value


@pyblock(category="data", is_predefined=True)
def data_listcontainsitem(context: Context, param_list: VariableRef, item: Any):
    var_value = __get_variable_list(context, param_list)

    for el in var_value:
        if el == item:
            return True
    return False


@pyblock(category="data", is_predefined=True)
async def data_deletealloflist(context: Context, param_list: VariableRef):
    context.set_variable(param_list, [])
    await context.next()


@pyblock(category="data", is_predefined=True)
async def data_showlist(context: Context, param_list: VariableRef):
    await context.next()


@pyblock(category="data", is_predefined=True)
async def data_hidelist(context: Context, param_list: VariableRef):
    await context.next()


data_blocks = collect_blocks(__name__)
