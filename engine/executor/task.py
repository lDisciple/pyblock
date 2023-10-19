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

    def __str__(self):
        return f"<Step:{self.name}>"
