from engine.blocks.block import pyblock, collect_blocks
from engine.executor.context import Context
from engine.executor.variable_reference import VariableRef


@pyblock(category="events", is_predefined=True, can_run=True)
def event_whenflagclicked(context: Context):
    def listener(topic, message):
        if topic == "executor" and message == "start":
            return context.next()

    context.listen(listener)


@pyblock(category="events", is_predefined=True, can_run=True)
def event_whenkeypressed(context: Context, key_option: str):
    def listener(topic, message):
        listen_key = key_option.replace(" arrow", "")
        if topic == "keyboard" and (key_option == "any" or message == listen_key):
            return context.next()

    context.listen(listener)


@pyblock(category="events", is_predefined=True, can_run=True)
def event_whenbroadcastreceived(context: Context, broadcast_option: VariableRef):
    broadcast_value: str = context.get_variable(broadcast_option)

    def listener(topic, received_message):
        if topic == "broadcast" and received_message == broadcast_value:
            return context.next()

    context.listen(listener)


@pyblock(category="events", is_predefined=True)
async def event_broadcast(context: Context, broadcast_input: VariableRef):
    broadcast_value: str = context.get_variable(broadcast_input)
    context.broadcast("broadcast", broadcast_value)
    await context.next()


event_blocks = collect_blocks(__name__)
