from typing import Callable
from xml.etree import ElementTree


class ExecutorStep:
    identifier: str
    name: str
    is_eager: bool

    def __init__(self, identifier: str, name: str, is_eager: bool):
        self.identifier = identifier
        self.name = name
        self.is_eager = is_eager

    def __await__(self):
        yield self  # This tells Task to wait for completion.
        return self.identifier


# class ExecutorTask:
#     element: ElementTree.Element
#     extra_kwargs: dict
#     is_eager: bool
#
#     def __init__(self, element: ElementTree, func: Callable, is_eager: bool, **kwargs):
#         self.element = element
#         self.func = func
#         self.is_eager = is_eager
#         self.extra_kwargs = kwargs
#
#     # def _resolve_kwargs(self):
#     #     return {k: v if not callable(v) else v for k, v in self.extra_kwargs.items()}
#     #
#     # def run(self):
#     #     return self.func()
#
#     def __await__(self):
#         yield self  # This tells Task to wait for completion.
#         kwargs = {}
#         for k, v in self.extra_kwargs.items():
#             if callable(v):
#                 kwargs[k] = v()
#             elif type(v) == ValueTask:
#                 kwargs[k] = yield v
#             else:
#                 kwargs[k] = v
#         return self.func()