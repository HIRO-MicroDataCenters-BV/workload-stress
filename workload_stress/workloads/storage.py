from typing import Any, cast

import os
import random
import tempfile
import time
from io import BytesIO
from multiprocessing import Process

from ..constants import MEGA
from ..logger import logger
from ..workload import WorkloadBase


class StorageWorkload(WorkloadBase):
    def __init__(self, **kwargs: dict[str, Any]) -> None:
        self.__time = cast(int, kwargs["time"])

        self.__proccess_count = cast(int, kwargs["storage_proccess_count"])
        self.__file_count = cast(int, kwargs["storage_file_count"])
        self.__file_min_size = cast(int, kwargs["storage_min_size"])
        self.__file_max_size = cast(int, kwargs["storage_max_size"])

        assert 1 <= self.__proccess_count, "Set the proccess count argument"
        assert 1 <= self.__time, "Set the time argument"
        assert 1 <= self.__file_count, "Set the file count argument"
        assert (
            1 <= self.__file_min_size < self.__file_max_size
        ), "Set the min and max size arguments"

    def run(self) -> None:
        logger.info("Run StorageWorkload")

        try:
            processes = []
            for _ in range(self.__proccess_count):
                process = Process(target=self.create_and_read_files)
                process.start()
                processes.append(process)

            for process in processes:
                process.join()
        except Exception as e:
            logger.exception(e)

    def _create_file(self, size_mb: int) -> tuple[BytesIO, int]:
        data: str | bytes
        num_bytes = int(size_mb * MEGA)

        data = bytes(random.getrandbits(8) for _ in range(num_bytes))

        file_stream = BytesIO()
        file_stream.write(data)
        file_stream.seek(0)

        return file_stream, num_bytes

    def create_and_read_files(self) -> None:
        logger.info("Create and read files")

        timeout = time.time() + self.__time

        while True:
            if time.time() > timeout:
                logger.info("Stop StorageWorkload by timer")
                break

            with tempfile.TemporaryDirectory() as temp_dir:
                for file_index in range(self.__file_count):
                    file_name = f"file{file_index}"
                    file_size = random.randint(
                        self.__file_min_size, self.__file_max_size
                    )
                    file_stream, file_size = self._create_file(size_mb=file_size)

                    file_path = os.path.join(temp_dir, file_name)
                    with open(file_path, "wb") as f:
                        f.write(file_stream.getbuffer())

                for file_index in range(self.__file_count):
                    file_name = f"file{file_index}"
                    file_path = os.path.join(temp_dir, file_name)
                    with open(file_path, "rb") as f:
                        BytesIO(f.read())
