import abc

class Step(abc.ABC):
    def __init__(self, context):
        self.context = context

    @abc.abstractmethod
    def execute(self):
        """Execute the step logic."""
        pass
