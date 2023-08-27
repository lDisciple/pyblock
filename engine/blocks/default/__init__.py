from engine.blocks.default.control import control_blocks
from engine.blocks.default.data import data_blocks
from engine.blocks.default.events import event_blocks
from engine.blocks.default.operators import operator_blocks

default_blocks = [
    *control_blocks,
    *operator_blocks,
    *data_blocks,
    *event_blocks
]
