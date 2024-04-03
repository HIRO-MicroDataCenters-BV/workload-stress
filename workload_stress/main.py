import signal

from .logger import logger
from .runner import Runner
from .workloads.cpu import CpuWorkload
from .workloads.memory import MemoryWorkload
from .workloads.minio import MinioWorkload


def run_workload_stress(
    cpu,
    time,
    ram,
    minio_host,
    minio_access_key,
    minio_secret_key,
    minio_bucket_count,
    minio_file_count,
    minio_min_size,
    minio_max_size,
):
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    logger.info("Run workload-stress with:")
    logger.info(f"time (s): {time}")
    logger.info(f"cpu (%): {cpu}")
    logger.info(f"ram (%): {ram}")
    logger.info(f"minio_host: {minio_host}")
    logger.info("minio_access_key: ***")
    logger.info("minio_secret_key: ***")
    logger.info(f"minio_bucket_count: {minio_bucket_count}")
    logger.info(f"minio_file_count: {minio_file_count}")
    logger.info(f"minio_min_size (Mb): {minio_min_size}")
    logger.info(f"minio_max_size (Mb): {minio_max_size}")

    workloads = [
        CpuWorkload,
        MemoryWorkload,
        MinioWorkload,
    ]
    runner = Runner(workloads)
    runner.run(
        cpu=cpu,
        time=time,
        ram=ram,
        minio_host=minio_host,
        minio_access_key=minio_access_key,
        minio_secret_key=minio_secret_key,
        minio_bucket_count=minio_bucket_count,
        minio_file_count=minio_file_count,
        minio_min_size=minio_min_size,
        minio_max_size=minio_max_size,
    )
