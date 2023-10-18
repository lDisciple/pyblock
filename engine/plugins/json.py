import json

from engine.blocks.block import PyBlockDefinition, pyblock, collect_blocks
from engine.blocks.fields import Variable
from engine.blocks.inputs import InputValue
from engine.executor.context import Context
from engine.executor.variable_reference import VariableRef

category = "json"
color = 93


@pyblock(
    category=category,
    definition=PyBlockDefinition(
        title="Parse JSON from %1",
        arguments=[
            InputValue(name="STRING")
        ],
        color=color,
        extensions=["output_string"]
    )
)
def json_parse(context: Context, string: str):
    return json.loads(string)

@pyblock(
    category=category,
    definition=PyBlockDefinition(
        title="Get %1 from %2",
        arguments=[
            InputValue(name="KEY"),
            InputValue(name="OBJ"),
        ],
        color=color,
        extensions=["output_string"]
    )
)
def json_value(context: Context, key: str, obj: dict | list | str):
    if type(obj) == str:
        obj = json.loads(obj)
    if type(obj) == list:
        return obj[int(key)]
    return obj[key]

@pyblock(
    category=category,
    definition=PyBlockDefinition(
        title="Assign JSON Array %1 to %2",
        arguments=[
            InputValue(name="VALUE"),
            Variable(name="VARIABLE_LIST", variableTypes=['list']),
        ],
        has_next_statement=True,
        has_previous_statement=True,
        color=color
    )
)
async def json_array_to_list(context: Context, value: list | str, variable_list: VariableRef):
    if type(value) == str:
        value = json.loads(value)
    context.set_variable(variable_list, list(value))
    await context.next()


json_blocks = collect_blocks(__name__)
