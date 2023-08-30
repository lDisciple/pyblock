import string

import pyperclip
from pynput.keyboard import Key, Controller

from engine.blocks.block import pyblock, PyBlockDefinition, collect_blocks
from engine.blocks.fields import Dropdown
from engine.blocks.inputs import InputValue
from engine.executor.context import Context

keyboard = Controller()

category = "keyboard"
color = 176

key_list = ([(letter, letter) for letter in string.ascii_lowercase + string.digits] +
            [(k.name, k.name) for k in Key])


def resolve_key(key: str):
    if len(key) > 1:
        return Key[key]
    return key


@pyblock(
    category=category,
    can_run=True,
    definition=PyBlockDefinition(
        title="When %1 key is pressed",
        arguments=[
            Dropdown(name="KEY_OPTION", options=[
                ("Insert", "insert"),
                ("Control", "ctrl"),
                ("Tab", "tab")
            ])
        ],
        has_next_statement=True,
        has_previous_statement=False,
        color=color
    )
)
def keyboard_whenkeypressed(context: Context, key_option: str):
    def listener(topic, message):
        if topic == "keyboard" and message == key_option:
            context.next()

    context.listen(listener)


@pyblock(
    category=category,
    definition=PyBlockDefinition(
        title="Next pane (ctrl + down)",
        has_next_statement=True,
        has_previous_statement=True,
        color=color
    )
)
def next_pane(context: Context):
    with keyboard.pressed(Key.ctrl):
        keyboard.press(Key.page_down)
        keyboard.release(Key.page_down)
    context.next()


@pyblock(
    category=category,
    definition=PyBlockDefinition(
        title="Previous pane (ctrl + pageUp)",
        has_next_statement=True,
        has_previous_statement=True,
        color=color
    )
)
def prev_pane(context: Context):
    with keyboard.pressed(Key.ctrl):
        keyboard.press(Key.page_up)
        keyboard.release(Key.page_up)
    context.next()


@pyblock(
    category=category,
    definition=PyBlockDefinition(
        title="Next record (shift + down)",
        has_next_statement=True,
        has_previous_statement=True,
        color=color
    )
)
def next_record(context: Context):
    with keyboard.pressed(Key.shift):
        keyboard.press(Key.down)
        keyboard.release(Key.down)
    context.next()


@pyblock(
    category=category,
    definition=PyBlockDefinition(
        title="Previous Record (shift + up)",
        has_next_statement=True,
        has_previous_statement=True,
        color=color
    )
)
def prev_record(context: Context):
    with keyboard.pressed(Key.shift):
        keyboard.press(Key.up)
        keyboard.release(Key.up)
    context.next()


@pyblock(
    category=category,
    definition=PyBlockDefinition(
        title="Next field (tab)",
        has_next_statement=True,
        has_previous_statement=True,
        color=color
    )
)
def next_field(context: Context):
    keyboard.press(Key.tab)
    keyboard.release(Key.tab)
    context.next()


@pyblock(
    category=category,
    definition=PyBlockDefinition(
        title="Go to first record (pageUp)",
        has_next_statement=True,
        has_previous_statement=True,
        color=color
    )
)
def go_to_first_record(context: Context):
    keyboard.press(Key.page_up)
    keyboard.release(Key.page_up)
    context.next()


@pyblock(
    category=category,
    definition=PyBlockDefinition(
        title="Type %1",
        arguments=[
            InputValue(name="TEXT")
        ],
        has_next_statement=True,
        has_previous_statement=True,
        color=color
    )
)
def type_text(context: Context, text: str):
    keyboard.type(str(text))
    context.next()


@pyblock(
    category=category,
    definition=PyBlockDefinition(
        title="Press %1",
        arguments=[
            Dropdown(name="KEY", options=key_list)
        ],
        has_next_statement=True,
        has_previous_statement=True,
        color=color
    )
)
def press_key(context: Context, key: str):
    keyboard.press(resolve_key(key))
    context.next()


@pyblock(
    category=category,
    definition=PyBlockDefinition(
        title="Release %1",
        arguments=[
            Dropdown(name="KEY", options=key_list)
        ],
        has_next_statement=True,
        has_previous_statement=True,
        color=color
    )
)
def release_key(context: Context, key: str):
    keyboard.release(resolve_key(key))
    context.next()


@pyblock(
    category=category,
    definition=PyBlockDefinition(
        title="Set clipboard to %1",
        arguments=[
            InputValue(name="TEXT")
        ],
        has_next_statement=True,
        has_previous_statement=True,
        color=color
    )
)
def set_clipboard_to(context: Context, text: str):
    pyperclip.copy(text)
    context.next()


@pyblock(
    category=category,
    definition=PyBlockDefinition(
        title="Clipboard",
        color=color,
        extensions=["output_string"]
    )
)
def clipboard_value(context: Context):
    return pyperclip.paste()


keyboard_blocks = collect_blocks(__name__)
