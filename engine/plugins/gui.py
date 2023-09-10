import logging
import queue
import time
from threading import Thread
from typing import Callable, Optional

from pynput.keyboard import Controller

from engine.blocks.block import pyblock, PyBlockDefinition, collect_blocks
from engine.executor.block_call import BlockCall
from engine.executor.context import Context
from engine.blocks.fields import Variable, Dropdown
from engine.blocks.inputs import InputStatement, InputValue
from engine.executor.executor import Executor

from engine.executor.variable_reference import VariableRef

keyboard = Controller()

category = "gui"
color = 304


@pyblock(
    category=category,
    definition=PyBlockDefinition(
        title="Create GUI\nwith%1",
        arguments=[
            InputStatement(name="SUBSTACK")
        ],
        has_next_statement=True,
        has_previous_statement=True,
        color=color
    )
)
async def create_layout(context: Context, substack: BlockCall):
    gui_context: GuiPluginContext = context.get_plugin_context(GuiPluginContext.__name__)
    gui_context.create_gui()
    await substack()
    await context.next()


@pyblock(
    category=category,
    definition=PyBlockDefinition(
        title="Add panel with direction %1\n%2",
        arguments=[
            Dropdown(name="DIRECTION", options=[
                ("Left", "left"),
                ("Right", "right"),
                ("Top", "top"),
                ("Bottom", "bottom"),
            ]),
            InputStatement(name="SUBSTACK")
        ],
        has_next_statement=True,
        has_previous_statement=True,
        color=color
    )
)
async def add_panel(context: Context, direction: str, substack: BlockCall):
    gui_context: GuiPluginContext = context.get_plugin_context(GuiPluginContext.__name__)
    gui_context.add_inner_panel(direction)
    await substack()
    gui_context.leave_current_panel()
    await context.next()


@pyblock(
    category=category,
    definition=PyBlockDefinition(
        title="Add button %1 that broadcasts %2",
        arguments=[
            InputValue(name="TITLE"),
            Variable(name="BROADCAST_INPUT", variable="message", variableTypes=["broadcast_msg"])
        ],
        has_next_statement=True,
        has_previous_statement=True,
        color=color
    )
)
async def add_button(context: Context, title: str, broadcast_input: str):
    gui_context: GuiPluginContext = context.get_plugin_context(GuiPluginContext.__name__)
    gui_context.add_button(title, lambda: context.broadcast("broadcast", broadcast_input))
    await context.next()


@pyblock(
    category=category,
    definition=PyBlockDefinition(
        title="Add textfield %1 with value %2",
        arguments=[
            InputValue(name="TITLE"),
            Variable(name="VARIABLE", variable="textfield", variableTypes=[""])
        ],
        has_next_statement=True,
        has_previous_statement=True,
        color=color
    )
)
async def add_textfield(context: Context, title: str, variable: VariableRef):
    gui_context: GuiPluginContext = context.get_plugin_context(GuiPluginContext.__name__)
    gui_context.add_textfield(title, lambda x: context.set_variable(variable, x))
    await context.next()


@pyblock(
    category=category,
    definition=PyBlockDefinition(
        title="Add checkbox %1 with value %2",
        arguments=[
            InputValue(name="TITLE"),
            Variable(name="VARIABLE", variable="checkbox", variableTypes=[""])
        ],
        has_next_statement=True,
        has_previous_statement=True,
        color=color
    )
)
async def add_checkbox(context: Context, title: str, variable: VariableRef):
    gui_context: GuiPluginContext = context.get_plugin_context(GuiPluginContext.__name__)
    gui_context.add_checkbox(title, lambda x: context.set_variable(variable, x))
    await context.next()


@pyblock(
    category=category,
    definition=PyBlockDefinition(
        title="Show GUI",
        has_next_statement=True,
        has_previous_statement=True,
        color=color
    )
)
async def show_gui(context: Context):
    gui_context: GuiPluginContext = context.get_plugin_context(GuiPluginContext.__name__)
    gui_context.show()
    await context.next()


@pyblock(
    category=category,
    definition=PyBlockDefinition(
        title="Hide GUI",
        has_next_statement=True,
        has_previous_statement=True,
        color=color
    )
)
async def hide_gui(context: Context):
    gui_context: GuiPluginContext = context.get_plugin_context(GuiPluginContext.__name__)
    gui_context.hide()
    await context.next()


gui_blocks = collect_blocks(__name__)

import tkinter as tk


class GuiPluginContext:
    message_check_interval_ms = 200
    logger = logging.getLogger(__name__)
    thread: Thread
    active_element_stack: list[tuple[tk.Widget, str]]
    in_queue: queue.Queue
    root: Optional[tk.Tk]
    executor: Executor

    def __init__(self, executor: Executor):
        self.executor = executor

    @staticmethod
    def queue_call(func):
        def wrapper(self, *arg, **kw):
            self.in_queue.put(lambda: func(self, *arg, **kw))

        return wrapper

    def __enter__(self):
        self.active_element_stack = []
        self.in_queue = queue.Queue()
        self.root = None

        def start():
            self.root = tk.Tk()
            self.root.title('PyBlock GUI')
            self.root.group("")
            self.root.withdraw()
            self.root.after(self.message_check_interval_ms, self.check_queue())
            logging.info("Tkinter window started")
            self.root.mainloop()
            self.in_queue.put(None)
            self.root = None
            logging.info("Tkinter window closed")

        self.thread = Thread(target=start)
        self.thread.start()
        while self.root is None:
            time.sleep(1)

    def create_gui(self):
        pass
        # obj = self

    def check_queue(self):
        try:
            message = self.in_queue.get(block=False)
            if message is None:
                return

            if callable(message):
                try:
                    logging.debug("Found function on tkinter queue")
                    message()
                except Exception as e:
                    self.logger.error("GUI call failed", e)

            self.root.after(self.message_check_interval_ms, self.check_queue)
        except queue.Empty:
            # let's try again later
            self.root.after(self.message_check_interval_ms, self.check_queue)
            return

    def assert_gui_exists(self):
        if self.root is None:
            raise RuntimeError("No GUI has been created yet")

    @queue_call
    def show(self):
        self.assert_gui_exists()
        self.root.deiconify()

    @queue_call
    def hide(self):
        self.assert_gui_exists()
        self.root.withdraw()

    @queue_call
    def add_inner_panel(self, panel_direction: str):
        self.assert_gui_exists()
        panel, direction = self.get_current_panel()
        frame = tk.Frame()
        frame.pack(side=self.get_side(direction))
        self.active_element_stack.append((frame, panel_direction))

    @queue_call
    def leave_current_panel(self):
        self.active_element_stack.pop()

    def get_current_panel(self):
        self.assert_gui_exists()
        if len(self.active_element_stack) == 0:
            return self.root, "top"
        return self.active_element_stack[-1]

    @queue_call
    def add_button(self, title: str, callback: Callable):
        panel, direction = self.get_current_panel()
        button = tk.Button(panel, text=title, width=25, command=callback)
        button.pack(side=self.get_side(direction))

    @queue_call
    def add_checkbox(self, title: str, setter: Callable[[str], None]):
        panel, direction = self.get_current_panel()
        value = tk.IntVar()
        value.set(0)
        value.trace_add('write', lambda var, index, mode: setter("true" if value.get() else "false"))

        checkbox = tk.Checkbutton(panel,
                                  text=title,
                                  variable=value,
                                  onvalue=1,
                                  offvalue=0)
        checkbox.bind("<Button>", lambda x: value.get())
        checkbox.bind("<ButtonRelease>", lambda x: value.get())
        checkbox.pack(side=self.get_side(direction))

    @queue_call
    def add_textfield(self, title: str, setter: Callable[[str], None]):
        panel, direction = self.get_current_panel()
        value = tk.StringVar()
        value.set("")
        value.trace_add('write', lambda var, index, mode: setter(value.get()))

        frame = tk.Frame(panel)
        label = tk.Label(frame, text=title)
        label.grid(row=0, column=0)
        text = tk.Entry(frame, textvariable=value)
        text.bind("<Key>", lambda x: value.get())
        text.grid(row=0, column=1)
        frame.pack(side=self.get_side(direction))

    @queue_call
    def destroy(self):
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    @staticmethod
    def get_side(direction: str):
        if direction == "top":
            return tk.TOP
        if direction == "left":
            return tk.LEFT
        if direction == "bottom":
            return tk.BOTTOM
        if direction == "right":
            return tk.RIGHT
        return tk.TOP

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.root:
            logging.debug("Shutting down tkinter")
            self.destroy()
