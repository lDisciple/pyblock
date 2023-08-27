from abc import abstractmethod, ABC


class PyBlockParser(ABC):

    @abstractmethod
    def execute_block(self):
        pass
