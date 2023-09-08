from collections import deque
from threading import Thread
from typing import Coroutine

from engine.executor.task import ExecutorStep


class ExecutorTaskStack:
    task_list: deque[tuple[Coroutine, ExecutorStep]]
    task_counter: int

    def __init__(self, task_iteration_limit: int = 100_000):
        self.task_list = deque()
        self.task_iteration_limit = task_iteration_limit
        self.stopped = False

    def add_task(self, task):
        Thread(target=self._add_task, args=[task]).start()

    def _add_task(self, task):
        result_tuple = self._run_task_iteration(task)
        if result_tuple is not None:
            self.task_list.appendleft(result_tuple)

    def get_highlights(self):
        return [step.identifier for coro, step in self.task_list if step is not None]

    def complete(self):
        self.step(True)

    def step(self, until_completion=False):
        Thread(target=self._step, args=[until_completion]).start()

    def _step(self, until_completion=False):
        if len(self.task_list) == 0:
            return
        is_eager = True
        coro, step = self.task_list.popleft()
        while (is_eager or until_completion) and len(self.task_list) > 0 and not self.stopped:
            result_tuple = self._run_task_iteration(coro)
            if result_tuple is not None:
                coro, step = result_tuple
                # Run until first block result then skip through eager blocks
                is_eager = True if step is None else step.is_eager
                if not is_eager:
                    self.task_list.appendleft(result_tuple)
            else:
                is_eager = False

    def stop(self):
        self.stopped = True
        for coro, step in self.task_list:
            # ex = InterruptedError("Stopping executor") TODO
            # coro.throw(type(ex), ex, None)
            coro.close()
        self.task_list.clear()

    def __len__(self):
        return len(self.task_list)

    def _run_task_iteration(self, coro: Coroutine) -> tuple[Coroutine, ExecutorStep] | None:
        limit = self.task_iteration_limit
        while limit > 0 and not self.stopped:
            try:
                out_step = coro.send(None)
                if type(out_step) == ExecutorStep:
                    if not out_step.is_eager:
                        return coro, out_step
                else:
                    raise ValueError(f"Invalid awaitable type. Expected {ExecutorStep.__name__}")
            except StopIteration:
                return None
            limit -= 1
        if not self.stopped:
            raise RuntimeError(
                "Reached maximum iterations on task. Please investigate for an infinite recursion or loop")
