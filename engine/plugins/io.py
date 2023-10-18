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
async def io_print(context: Context, message: str):
    context.broadcast("print", message)
    await context.next()


@pyblock(
    category=category,
    definition=PyBlockDefinition(
        title="Read file %1",
        arguments=[
            InputValue(name="PATH")
        ],
        color=color,
        extensions=["output_string"]
    )
)
async def io_readfile(context: Context, path: str):
    with open(path, "r") as f:
        return "\n".join(f.readlines())


io_blocks = collect_blocks(__name__)
