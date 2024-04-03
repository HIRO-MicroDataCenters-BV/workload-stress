import argparse
import multiprocessing

from workload_stress.main import run_workload_stress

if __name__ == "__main__":
    multiprocessing.freeze_support()

    parser = argparse.ArgumentParser(description="Run workload for stress test.")
    parser.add_argument(
        "--time",
        type=int,
        default=60,
        help="Duration of the run in seconds",
    )
    parser.add_argument("--cpu", type=int, default=80, help="CPU workload percentage")
    parser.add_argument("--ram", type=int, default=90, help="RAM workload percentage")
    parser.add_argument(
        "--minio_host", type=str, default="localhost:9000", help="Minio host address"
    )
    parser.add_argument(
        "--minio_access_key",
        type=str,
        default="",
        help="Minio access key",
    )
    parser.add_argument(
        "--minio_secret_key",
        type=str,
        default="",
        help="Minio secret key",
    )
    parser.add_argument(
        "--minio_bucket_count", type=int, default=3, help="Number of Minio buckets"
    )
    parser.add_argument(
        "--minio_file_count",
        type=int,
        default=3,
        help="Number of files in Minio buckets",
    )
    parser.add_argument(
        "--minio_min_size",
        type=int,
        default=1,
        help="Minimum size of Minio files in MB",
    )
    parser.add_argument(
        "--minio_max_size",
        type=int,
        default=10,
        help="Maximum size of Minio files in MB",
    )
    args = parser.parse_args()

    run_workload_stress(
        args.cpu,
        args.time,
        args.ram,
        args.minio_host,
        args.minio_access_key,
        args.minio_secret_key,
        args.minio_bucket_count,
        args.minio_file_count,
        args.minio_min_size,
        args.minio_max_size,
    )
