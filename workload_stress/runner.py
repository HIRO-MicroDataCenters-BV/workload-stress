import multiprocessing

from .workload import WorkloadBase


class Runner:
    def __init__(self, workloads: list[type[WorkloadBase]]) -> None:
        self.__workloads = workloads
        self.__processes: list[multiprocessing.Process] = []

    def run(self, **kwargs):
        for workload_class in self.__workloads:
            workload = workload_class(**kwargs)
            process = multiprocessing.Process(target=workload.run)
            process.start()
            self.__processes.append(process)

        for process in self.__processes:
            process.join()
