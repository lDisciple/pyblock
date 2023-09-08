from typing import Protocol, Coroutine


class BlockCall(Protocol):
    def __call__(self, **kwargs) -> Coroutine:
        pass
