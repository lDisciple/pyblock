import time
from typing import Callable

from engine.blocks.block import pyblock, collect_blocks
from engine.executor.context import Context


@pyblock(category="control", is_predefined=True)
def control_wait(context: Context, duration: float):
    time.sleep(duration)
    context.next()


@pyblock(category="control", is_predefined=True)
def control_repeat(context: Context, substack: Callable, times: int):
    for i in range(int(times)):
        substack()
    context.next()


@pyblock(category="control", is_predefined=True)
def control_forever(context: Context, substack: Callable):
    substack()
    context.recurse()


@pyblock(category="control", is_predefined=True)
def control_if(context: Context, condition: bool, substack: Callable):
    if condition:
        substack()
    context.next()


@pyblock(category="control", is_predefined=True)
def control_if_else(context: Context, condition: bool, substack: Callable, substack2: Callable):
    if condition:
        substack()
    else:
        substack2()
    context.next()


@pyblock(category="control", is_predefined=True)
def control_wait_until(context: Context, condition: bool):
    if not condition:
        context.recurse()


@pyblock(category="control", is_predefined=True)
def control_repeat_until(context: Context, condition: bool, substack: Callable):
    if condition:
        substack()
        context.recurse()
    else:
        context.next()


@pyblock(category="control", is_predefined=True)
def control_stop(context: Context):
    pass


control_blocks = collect_blocks(__name__)
