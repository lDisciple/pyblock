from engine.blocks.block import PyBlockDefinition, pyblock, collect_blocks
from engine.blocks.inputs import InputValue
from engine.executor.context import Context

category = "io"
color = 200


@pyblock(
    category=category,
    definition=PyBlockDefinition(
        title="Print %1",
        arguments=[
            InputValue(name="MESSAGE")
        ],
        has_next_statement=True,
        has_previous_statement=True,
        color=color
    )
)
def io_print(context: Context, message: str):
    context.broadcast("print", message)
    context.next()


io_blocks = collect_blocks(__name__)
