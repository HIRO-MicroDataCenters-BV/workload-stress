from typing import Any, cast

import time

import psutil

from ..constants import MEGA, SLEEP_TIME
from ..logger import logger
from ..workload import WorkloadBase


class MemoryWorkload(WorkloadBase):
    def __init__(self, **kwargs: dict[str, Any]) -> None:
        self.__ram_max_persent = cast(int, kwargs["ram"])
        self.__time = cast(int, kwargs["time"])

        assert 1 <= self.__time, "Set the time argument"
        assert 1 <= self.__ram_max_persent <= 100, "Set the ram argument"

    def run(self) -> None:
        logger.info("Run MemoryWorkload")
        logger.info(f"time={self.__time}")
        logger.info(f"ram_max_persent={self.__ram_max_persent}")

        timeout = time.time() + self.__time
        arr = []

        try:
            while True:
                if time.time() > timeout:
                    logger.info("Stop MemoryWorkload by timer")
                    break

                if psutil.virtual_memory().percent > self.__ram_max_persent:
                    time.sleep(SLEEP_TIME)
                else:
                    try:
                        arr.append("x" * MEGA * 32)
                    except MemoryError:
                        pass
        except Exception as e:
            logger.exception(e)
        finally:
            del arr
