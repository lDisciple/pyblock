from typing import Protocol


class BlockCall(Protocol):
    def __call__(self, is_eager: bool = True, **kwargs) -> None:
        pass
