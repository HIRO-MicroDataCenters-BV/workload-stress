from abc import ABC, abstractmethod


class WorkloadBase(ABC):
    @abstractmethod
    def run(self) -> None:
        ...
