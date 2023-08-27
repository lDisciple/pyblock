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


data_blocks = collect_blocks(__name__)
