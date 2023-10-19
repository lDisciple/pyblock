import logging
import threading
import time
from functools import total_ordering
from queue import PriorityQueue, Empty, Queue, LifoQueue
from typing import Coroutine

from engine.executor.task import ExecutorStep

logger = logging.getLogger(__name__)


@total_ordering
class StackElement:
    priority: int
    coroutine: Coroutine
    executor_step: ExecutorStep | None

    def __init__(self, coroutine: Coroutine, executor_step: ExecutorStep | None, priority: int):
        self.coroutine = coroutine
        self.executor_step = executor_step
        self.priority = priority

    def __lt__(self, other):
        if type(other) is not StackElement:
            raise ValueError(f"Cannot compare {StackElement.__name__} with {other}")
        return self.priority < other.priority

    def __eq__(self, other):
        if type(other) is not StackElement:
            raise ValueError(f"Cannot compare {StackElement.__name__} with {other}")
        return self.priority == other.priority

    def __iter__(self):
        return iter((self.priority, self.coroutine, self.executor_step))


class ExecutorTaskStack:
    task_queue: PriorityQueue[StackElement]
    eager_queue: LifoQueue[StackElement]
    uninitialised_tasks: list[Coroutine]
    task_counter: int
    current_task: int
    highlights: set[str] = set()
    is_completing: bool
    is_running: bool
    thread: threading.Thread | None

    def __init__(self, task_iteration_limit: int = 100_000):
        self.task_queue = PriorityQueue()
        self.eager_queue = LifoQueue()
        self.uninitialised_tasks = []
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
            if executor_step is None:
                logger.debug(f"init queue: {coro}")
                self.uninitialised_tasks.append(coro)
                return
            is_eager = executor_step is None or executor_step.is_eager
            if not is_eager:
                priority = self.task_counter
                self.task_queue.put(StackElement(coro, executor_step, priority))
                logger.debug(f"Task queue: {executor_step} [{priority}]")
                self.task_counter += 1
            else:
                logger.debug(f"Eager queue: {executor_step}")
                self.eager_queue.put(StackElement(coro, executor_step, -1))

    def _pop_task(self, ):
        with self.lock:
            if self.eager_queue.qsize() > 0:
                item = self.eager_queue.get()
            else:
                item = self.task_queue.get()
            logger.debug(f"Pop queue: {item.executor_step}")
            return item

    def _is_empty(self):
        return self.eager_queue.qsize() == 0 and self.task_queue.qsize() == 0

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

    def _execute_coro(self, coro: Coroutine, step: ExecutorStep | None) -> ExecutorStep:
        self.remove_highlight(step)
        out_step = coro.send(None)
        logger.debug(f"Step {out_step}")
        if type(out_step) is ExecutorStep:
            self.add_highlight(out_step)
            self._add_task(coro, out_step)
            return out_step
        else:
            raise ValueError(f"Invalid awaitable type. Expected {ExecutorStep.__name__}")

    def run(self):
        if not self.thread or not self.thread.isAlive():
            self.thread = threading.Thread(target=self._run)
            self.thread.start()

    def _run(self):
        logger.info("Started ExecutorTaskStack thread")
        self.is_running = True
        while self.is_running:
            if len(self.uninitialised_tasks) > 0:
                tasks = self.uninitialised_tasks
                self.uninitialised_tasks = []
                logger.debug(f"Init tasks: {len(tasks)}")
                for coro in reversed(tasks):
                    try:
                        self._execute_coro(coro, None)
                    except StopIteration:
                        pass
            if self._is_empty():
                self.is_completing = False
                self.task_counter = 0
                self.current_task = -1
                time.sleep(0.1)
                continue
            item = self._pop_task()
            priority, coro, step = item
            if priority > self.current_task and not self.is_completing:
                self.add_highlight(step)
                self.task_queue.put(item)  # Put exact item back into task_queue (eager tasks should not reach here)
                time.sleep(0.1)
            else:
                try:
                    self._execute_coro(coro, step)
                except StopIteration:
                    pass
        logger.info("Stopped ExecutorTaskStack thread")

    def stop(self):
        self.is_running = False
        try:
            while True:
                item = self.task_queue.get_nowait()
                item.coroutine.close()
        except Empty:
            pass
        try:
            while True:
                item = self.eager_queue.get_nowait()
                item.coroutine.close()
        except Empty:
            pass
        self.highlights.clear()
        if self.thread:
            self.thread.join()

    def __len__(self):
        return self.task_queue.qsize() + self.eager_queue.qsize() + len(self.uninitialised_tasks)
