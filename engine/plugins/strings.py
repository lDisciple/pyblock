from engine.blocks.block import pyblock, PyBlockDefinition, collect_blocks
from engine.blocks.fields import Variable
from engine.blocks.inputs import InputValue
from engine.executor.context import Context
from engine.executor.variable_reference import VariableRef

operator_color = "#59C059"


@pyblock(
    category="operators",
    definition=PyBlockDefinition(
        title="trim %1",
        arguments=[
            InputValue(name="STRING")
        ],
        color=operator_color,
        extensions=["output_string"]
    )
)
def string_trim(context: Context, string: str):
    return str(string).strip()


@pyblock(
    category="operators",
    definition=PyBlockDefinition(
        title="split %1 on %2 to %3",
        arguments=[
            InputValue(name="STRING"),
            InputValue(name="CHARS"),
            Variable(name="VARIABLE", variable="list", variableTypes=["list"])
        ],
        has_next_statement=True,
        has_previous_statement=True,
        color=operator_color
    )
)
def string_splitvar(context: Context, string: str, chars: str, variable: VariableRef):
    context.set_variable(variable, str(string).split(str(chars)))
    context.next()


@pyblock(
    category="operators",
    definition=PyBlockDefinition(
        title="split %1 on %2",
        arguments=[
            InputValue(name="STRING"),
            InputValue(name="CHARS")
        ],
        color=operator_color,
        extensions=["output_string"]
    )
)
def string_split(context: Context, string: str, chars: str):
    return str(string).split(str(chars))


@pyblock(
    category="operators",
    definition=PyBlockDefinition(
        title="substring from %1 to %2 of %3",
        arguments=[
            InputValue(name="START"),
            InputValue(name="END"),
            InputValue(name="STRING")
        ],
        color=operator_color,
        extensions=["output_string"]
    )
)
def string_substring(context: Context, string: str, start: int, end: int):
    return str(string)[int(start): int(end)]


strings_blocks = collect_blocks(__name__)
