from pynput.keyboard import Listener, KeyCode, Key

from engine.executor.executor import Executor


class CorePluginContext:
    executor: Executor
    key_listener: Listener

    def __init__(self, executor: Executor):
        self.executor = executor

    @staticmethod
    def queue_call(func):
        def wrapper(self, *arg, **kw):
            self.in_queue.put(lambda: func(self, *arg, **kw))

        return wrapper

    def create_listener(self):
        def on_release(key: (Key | KeyCode | None)):
            if self.executor.is_complete():
                return
            if key is None:
                return
            if type(key) == Key:
                self.executor.broadcast("keyboard", key.name)
            if type(key) == KeyCode:
                self.executor.broadcast("keyboard", key.char)

        # Collect events until released
        self.key_listener = Listener(on_release=on_release)
        self.key_listener.start()

    def __enter__(self):
        self.create_listener()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.key_listener.stop()
