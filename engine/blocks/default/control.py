import time
from typing import Callable

from engine.blocks.block import pyblock, collect_blocks
from engine.executor.block_call import BlockCall
from engine.executor.context import Context
from engine.executor.value import Value


@pyblock(category="control", is_predefined=True)
async def control_wait(context: Context, duration: float):
    time.sleep(duration)
    await context.next()


@pyblock(category="control", is_predefined=True)
async def control_repeat(context: Context, substack: BlockCall, times: int):
    for i in range(int(times)):
        await substack()
    await context.next()


@pyblock(category="control", is_predefined=True)
async def control_forever(context: Context, substack: BlockCall):
    while True:
        await substack()


@pyblock(category="control", is_predefined=True)
async def control_if(context: Context, condition: bool, substack: BlockCall):
    if condition:
        await substack()
    await context.next()


@pyblock(category="control", is_predefined=True)
async def control_if_else(context: Context, condition: bool, substack: BlockCall, substack2: BlockCall):
    if condition:
        await substack()
    else:
        await substack2()
    await context.next()


@pyblock(category="control", is_predefined=True)
async def control_wait_until(context: Context, condition: bool):
    if not condition:
        await context.recurse()


@pyblock(category="control", is_predefined=True)
async def control_repeat_until(context: Context, condition: Value[bool], substack: BlockCall):
    while await condition.get():
        await substack()
    await context.next()


@pyblock(category="control", is_predefined=True)
async def control_stop(context: Context):
    pass


control_blocks = collect_blocks(__name__)
