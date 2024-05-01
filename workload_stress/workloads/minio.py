from typing import Any, cast

import random
import time
import uuid
from io import BytesIO
from multiprocessing import Process

from minio import Minio
from minio.helpers import ObjectWriteResult

from ..constants import MEGA
from ..logger import logger
from ..workload import WorkloadBase


class MinIOFileManager:
    def __init__(self, host: str, access_key: str, secret_key: str) -> None:
        assert host, "Set the MinIO host argument"
        assert access_key, "Set the MinIO access key argument"
        assert secret_key, "Set the MinIO secret key argument"

        self.__host = host
        self.__access_key = access_key
        self.__secret_key = secret_key

    def connect(self) -> None:
        self.__client = Minio(
            self.__host,
            access_key=self.__access_key,
            secret_key=self.__secret_key,
            cert_check=False,
            # secure=False,
        )

    def create_uniq_bucket(self) -> str:
        while True:
            bucket_name = str(uuid.uuid1())
            if not self.__client.bucket_exists(bucket_name):
                self.__client.make_bucket(bucket_name)
                break
        return bucket_name

    def remove_bucket(self, bucket_name: str) -> None:
        objects = self.__client.list_objects(bucket_name, recursive=True)
        for obj in objects:
            self.__client.remove_object(bucket_name, obj.object_name)

        self.__client.remove_bucket(bucket_name)

    def upload_file(
        self,
        bucket_name: str,
        file_name: str,
        stream: BytesIO,
        size: int,
    ) -> ObjectWriteResult:
        return self.__client.put_object(
            bucket_name,
            file_name,
            stream,
            size,
        )

    def move_file(
        self,
        file_name: str,
        source_bucket_name: str,
        destination_bucket_name: str,
    ) -> None:
        object_data = self.__client.get_object(source_bucket_name, file_name)

        self.__client.put_object(
            bucket_name=destination_bucket_name,
            object_name=file_name,
            data=BytesIO(object_data.data),
            length=int(object_data.headers["content-length"]),
        )

        self.__client.remove_object(source_bucket_name, file_name)


class MinioWorkload(WorkloadBase):
    def __init__(self, **kwargs: dict[str, Any]) -> None:
        self.__kwargs = kwargs
        self.__file_manager_class = MinIOFileManager

        self.__buckets: list[str] = []
        self.__files: list[dict[str, Any]] = []

    def setup(self):
        self.__time = cast(int, self.__kwargs["time"])

        self.__minio_host = cast(str, self.__kwargs["minio_host"])
        self.__minio_access_key = cast(str, self.__kwargs["minio_access_key"])
        self.__minio_secret_key = cast(str, self.__kwargs["minio_secret_key"])
        self.__bucket_count = cast(int, self.__kwargs["minio_bucket_count"])
        self.__minio_file_count = cast(int, self.__kwargs["minio_file_count"])
        self.__minio_min_size = cast(int, self.__kwargs["minio_min_size"])
        self.__minio_max_size = cast(int, self.__kwargs["minio_max_size"])

        assert 1 <= self.__time, "Set the time argument"
        assert 2 <= self.__bucket_count, "Set the bucket count argument"
        assert 1 <= self.__minio_file_count, "Set the file count argument"
        assert (
            1 <= self.__minio_min_size < self.__minio_max_size
        ), "Set the min and max size arguments"

        self.__file_manager = self.__file_manager_class(
            host=self.__minio_host,
            access_key=self.__minio_access_key,
            secret_key=self.__minio_secret_key,
        )
        self.__file_manager.connect()

    def run(self) -> None:
        logger.info("Run MinioWorkload")
        logger.info(f"kwargs={self.__kwargs}")
        logger.info(f"file_manager_class={self.__file_manager_class}")

        self.setup()

        try:
            self._create_buckets()
            self._create_and_distribute_files()

            processes = []
            for file_in_bucket in self.__files:
                file_name = file_in_bucket["file_name"]
                bucket_index = file_in_bucket["bucket_index"]
                bucket_name = file_in_bucket["bucket_name"]

                process = Process(
                    target=self.rotate_file,
                    args=(
                        file_name,
                        bucket_index,
                        bucket_name,
                        self.__buckets,
                        self.__kwargs,
                    ),
                )
                process.start()
                processes.append(process)

            for process in processes:
                process.join()
        except Exception as e:
            logger.exception(e)
        finally:
            self._remove_buckets()

    @classmethod
    def rotate_file(
        cls,
        file_name: str,
        bucket_index: int,
        bucket_name: str,
        buckets: list[Any],
        kwargs: dict[str, Any],
    ) -> None:
        instance = cls(**kwargs)
        instance.setup()
        instance.__buckets = buckets

        logger.info(f"Rotate file {file_name}")

        timeout = time.time() + instance.__time

        while True:
            if time.time() > timeout:
                logger.info("Stop MinioWorkload by timer")
                break

            next_bucket_index = (bucket_index + 1) % instance.__bucket_count
            next_bucket_name = instance.__buckets[next_bucket_index]

            instance._move_file(file_name, bucket_name, next_bucket_name)

            bucket_index = next_bucket_index
            bucket_name = next_bucket_name

    def _create_buckets(self) -> None:
        logger.info("Create buckets")

        for _ in range(self.__bucket_count):
            self.__buckets.append(self.__file_manager.create_uniq_bucket())

    def _remove_buckets(self) -> None:
        logger.info("Remove all buckets")

        for bucket_name in self.__buckets:
            self.__file_manager.remove_bucket(bucket_name)

    def _create_file(self, size_mb: int) -> tuple[BytesIO, int]:
        logger.info(f"Create new file {size_mb} Mb")

        data: str | bytes
        num_bytes = int(size_mb * MEGA)

        data = bytes(random.getrandbits(8) for _ in range(num_bytes))

        file_stream = BytesIO()
        file_stream.write(data)
        file_stream.seek(0)

        return file_stream, num_bytes

    def _create_and_distribute_files(self) -> None:
        logger.info("Create and distribute files")

        for file_index in range(self.__minio_file_count):
            bucket_index = file_index % self.__bucket_count
            bucket_name = self.__buckets[bucket_index]

            file_name = f"file{file_index}"
            file_size = random.randint(self.__minio_min_size, self.__minio_max_size)
            file_stream, file_size = self._create_file(size_mb=file_size)

            self.__file_manager.upload_file(
                bucket_name, file_name, file_stream, file_size
            )

            self.__files.append(
                {
                    "file_index": file_index,
                    "file_name": file_name,
                    "file_size": file_size,
                    "bucket_index": bucket_index,
                    "bucket_name": bucket_name,
                }
            )

    def _move_file(
        self,
        file_name: str,
        bucket_name: str,
        next_bucket_name: str,
    ) -> None:
        logger.info(f"Move file {file_name} from {bucket_name} to {next_bucket_name}")
        self.__file_manager.move_file(file_name, bucket_name, next_bucket_name)
