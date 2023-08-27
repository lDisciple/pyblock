from engine.blocks.block import pyblock, collect_blocks
from engine.executor.context import Context


@pyblock(category="events", is_predefined=True, can_run=True)
def event_whenflagclicked(context: Context):
    def listener(topic, message):
        if topic == "executor" and message == "start":
            context.next()

    context.listen(listener)


@pyblock(category="events", is_predefined=True, can_run=True)
def event_whenkeypressed(context: Context, key_option: str):
    def listener(topic, message):
        listen_key = key_option.replace(" arrow", "")
        if topic == "keyboard" and (key_option == "any" or message == listen_key):
            context.next()
    context.listen(listener)


@pyblock(category="events", is_predefined=True, can_run=True)
def event_whenbroadcastreceived(context: Context, broadcast_option: str):
    def listener(topic, received_message):
        if topic == "broadcast" and received_message == broadcast_option:
            context.next()

    context.listen(listener)


@pyblock(category="events", is_predefined=True)
def event_broadcast(context: Context, broadcast_input: str):
    context.broadcast("broadcast", broadcast_input)
    context.next()


event_blocks = collect_blocks(__name__)
