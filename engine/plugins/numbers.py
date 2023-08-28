from typing import Any

from engine.blocks.block import pyblock, PyBlockDefinition, collect_blocks
from engine.blocks.inputs import InputValue
from engine.executor.context import Context

operator_color = "#59C059"


@pyblock(
    category="operators",
    definition=PyBlockDefinition(
        title="is %1 numeric",
        arguments=[
            InputValue(name="VALUE")
        ],
        color=operator_color,
        extensions=["output_boolean"]
    )
)
def numbers_isnumeric(context: Context, value: Any):
    try:
        float(value)
        return True
    except:
        return False


numbers_blocks = collect_blocks(__name__)
