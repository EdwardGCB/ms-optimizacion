from abc import ABC, abstractmethod


class BaseService(ABC):

    def __init__(self, alias: str, orchestrator, temp_data=None):
        self.orchestrator = orchestrator
        self.alias = alias
        self.temp_data = temp_data
        self.stop_orchestrator = False  # To stop orchestrator

    def setup(self, **kwargs):
        """
        Setup the service before run. Overload this method if additional data
        for run the service is required.
        """
        pass

    @abstractmethod
    async def run(self):
        """
        Main menthod of the service. The logic associated with the execution of
        the service go here
        """
        pass

    def store_temporal_data(self):
        if self.temp_data:
            self.orchestrator.payload[self.alias] = self.temp_data
