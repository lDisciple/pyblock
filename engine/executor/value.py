from typing import Callable, TypeVar, Generic, Awaitable, Coroutine

from engine.executor.variable_reference import VariableRef

T = TypeVar("T")


class Value(Generic[T]):
    variable_ref: VariableRef | None
    getter: Callable[[], Awaitable[T]]

    def __init__(self, getter: Callable[[], Awaitable[T]], variable_ref: VariableRef = None):
        self.getter = getter
        self.variable_ref = variable_ref

    def get(self) -> Awaitable[T]:
        return self.getter()

    def is_variable(self) -> bool:
        return self.variable_ref is not None

    def get_variable_reference(self) -> VariableRef | None:
        return self.variable_ref


class StatementValue(Value):
    getter: Callable[[bool], Awaitable[T]]

    def __init__(self, getter: Callable[[bool], Awaitable[T]]):
        super().__init__(getter, None)

    def get(self, is_eager=True) -> Awaitable[T]:
        return self.getter(is_eager)
