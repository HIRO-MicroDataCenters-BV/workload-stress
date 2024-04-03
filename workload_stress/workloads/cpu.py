from typing import Any, cast

import os
import time
from multiprocessing import Process

import psutil

from ..constants import SLEEP_TIME
from ..logger import logger
from ..workload import WorkloadBase


class CpuWorkload(WorkloadBase):
    def __init__(self, **kwargs: dict[str, Any]) -> None:
        self.__cpu_max_persent = cast(int, kwargs["cpu"])
        self.__time = cast(int, kwargs["time"])
        self.__cpu_count = os.cpu_count() or 1

        assert 1 <= self.__time, "Set the time argument"
        assert 1 <= self.__cpu_max_persent <= 100, "Set the cpu argument"

    def run(self) -> None:
        logger.info("Run CpuWorkload")
        logger.info(f"time={self.__time}")
        logger.info(f"cpu_count={self.__cpu_count}")
        logger.info(f"cpu_max_persent={self.__cpu_max_persent}")

        processes = []
        for _ in range(self.__cpu_count):
            process = Process(target=self._one_cpu_workload)
            process.start()
            processes.append(process)

    def _one_cpu_workload(self) -> None:
        timeout = time.time() + self.__time

        while True:
            if time.time() > timeout:
                logger.info("Stop CpuWorkload by timer")
                break

            if psutil.cpu_percent() > self.__cpu_max_persent:
                time.sleep(SLEEP_TIME)
            else:
                2 * 2
