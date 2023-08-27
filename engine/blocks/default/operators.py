import math
import random

from engine.blocks.block import pyblock, collect_blocks
from engine.executor.context import Context


@pyblock(category="operators", is_predefined=True)
def operator_add(context: Context, operand1: float, operand2: float):
    return float(operand1) + float(operand2)


@pyblock(category="operators", is_predefined=True)
def operator_subtract(context: Context, operand1: float, operand2: float):
    return float(operand1) - float(operand2)


@pyblock(category="operators", is_predefined=True)
def operator_multiply(context: Context, operand1: float, operand2: float):
    return float(operand1) * float(operand2)


@pyblock(category="operators", is_predefined=True)
def operator_divide(context: Context, operand1: float, operand2: float):
    return float(operand1) / float(operand2)


@pyblock(category="operators", is_predefined=True)
def operator_mod(context: Context, operand1: float, operand2: float):
    return float(operand1) % float(operand2)


@pyblock(category="operators", is_predefined=True)
def operator_random(context: Context, **kwargs):
    return random.randrange(int(kwargs["from"]), int(kwargs["to"]))


@pyblock(category="operators", is_predefined=True)
def operator_lt(context: Context, operand1: float, operand2: float):
    return float(operand1) < float(operand2)


@pyblock(category="operators", is_predefined=True)
def operator_equals(context: Context, operand1: float, operand2: float):
    return float(operand1) == float(operand2)


@pyblock(category="operators", is_predefined=True)
def operator_gt(context: Context, operand1: float, operand2: float):
    return operand1 > float(operand2)


@pyblock(category="operators", is_predefined=True)
def operator_round(context: Context, value: float):
    return round(value)


@pyblock(category="operators", is_predefined=True)
def operator_and(context: Context, operand1: bool, operand2: bool):
    return operand1 and operand2


@pyblock(category="operators", is_predefined=True)
def operator_or(context: Context, operand1: bool, operand2: bool):
    return operand1 or operand2


@pyblock(category="operators", is_predefined=True)
def operator_not(context: Context, operand1: bool):
    return not operand1


@pyblock(category="operators", is_predefined=True)
def operator_join(context: Context, operand1: str, operand2: str):
    return operand1 + operand2


@pyblock(category="operators", is_predefined=True)
def operator_letter_of(context: Context, letter: int, string: str):
    return string[letter]


@pyblock(category="operators", is_predefined=True)
def operator_length(context: Context, value: str):
    return len(value)


@pyblock(category="operators", is_predefined=True)
def operator_contains(context: Context, string1: str, string2: str):
    return string2 in string1


@pyblock(category="operators", is_predefined=True)
def operator_mathop(context: Context, operator: str, num: float):
    num = float(num)
    if operator == "abs":
        return abs(num)
    if operator == "floor":
        return math.floor(num)
    if operator == "ceiling":
        return math.ceil(num)
    if operator == "sqrt":
        return math.sqrt(num)
    if operator == "sin":
        return math.sin(num)
    if operator == "cos":
        return math.cos(num)
    if operator == "tan":
        return math.tan(num)
    if operator == "asin":
        return math.asin(num)
    if operator == "acos":
        return math.acos(num)
    if operator == "atan":
        return math.atan(num)
    if operator == "ln":
        return math.log(num)
    if operator == "log":
        return math.log10(num)
    if operator == "e ^":
        return math.e ** num
    if operator == "10 ^":
        return 10 ** num


operator_blocks = collect_blocks(__name__)
