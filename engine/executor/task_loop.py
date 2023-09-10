import logging
import threading
import time
from queue import PriorityQueue, Empty
from typing import Coroutine

from engine.executor.task import ExecutorStep

logger = logging.getLogger(__name__)


class ExecutorTaskStack:
    queue: PriorityQueue[tuple[int, Coroutine, ExecutorStep | None]]
    task_counter: int
    current_task: int
    highlights: set[str] = set()
    is_completing: bool
    is_running: bool
    thread: threading.Thread | None

    def __init__(self, task_iteration_limit: int = 100_000):
        self.queue = PriorityQueue()
        self.lock = threading.Lock()
        self.is_completing = False
        self.is_running = False
        self.task_counter = 0
        self.current_task = -1
        self.task_iteration_limit = task_iteration_limit
        self.stopped = False
        self.thread = None

    def add_task(self, coro: Coroutine):
        # Initial task steps are always eager
        self._add_task(coro, executor_step=None)

    def _add_task(self, coro: Coroutine, executor_step: ExecutorStep | None):
        with self.lock:
            is_eager = executor_step is None or executor_step.is_eager
            priority = -1
            if not is_eager:
                priority = self.task_counter
                self.task_counter += 1
            self.queue.put((priority, coro, executor_step))

    def _pop_task(self, ):
        with self.lock:
            item = self.queue.get()
            _, _, step = item
            return item

    def get_highlights(self):
        return self.highlights

    def remove_highlight(self, executor_step: ExecutorStep):
        if executor_step is not None and executor_step.identifier in self.highlights:
            self.highlights.remove(executor_step.identifier)

    def add_highlight(self, executor_step: ExecutorStep):
        if executor_step is not None and executor_step.is_eager is False:
            self.highlights.add(executor_step.identifier)

    def complete(self):
        self.is_completing = True

    def step(self):
        self.current_task += 1

    def wait_until_complete(self):
        self.is_completing = True
        while self.is_completing:
            time.sleep(0.1)

    def run(self):
        if not self.thread or not self.thread.isAlive():
            self.thread = threading.Thread(target=self._run)
            self.thread.start()

    def _run(self):
        logger.info("Started ExecutorTaskStack thread")
        self.is_running = True
        while self.is_running:
            if self.queue.empty():
                self.is_completing = False
                self.task_counter = 0
                self.current_task = -1
                time.sleep(0.1)
                continue
            item = self._pop_task()
            priority, coro, step = item
            if priority > self.current_task and not self.is_completing:
                self.add_highlight(step)
                self.queue.put(item)  # Put exact item back
                time.sleep(0.1)
            else:
                try:
                    self.remove_highlight(step)
                    out_step = coro.send(None)
                    if type(out_step) == ExecutorStep:
                        self.add_highlight(out_step)
                        self._add_task(coro, out_step)
                    else:
                        raise ValueError(f"Invalid awaitable type. Expected {ExecutorStep.__name__}")
                except StopIteration:
                    pass
        logger.info("Stopped ExecutorTaskStack thread")

    def stop(self):
        self.is_running = False
        try:
            while True:
                self.queue.get_nowait()
        except Empty:
            pass
        self.highlights.clear()
        if self.thread:
            self.thread.join()

    def __len__(self):
        return 0 if self.queue.empty() else self.queue.qsize()
