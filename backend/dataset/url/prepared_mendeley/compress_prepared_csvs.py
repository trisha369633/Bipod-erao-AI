"""Losslessly gzip the prepared URL CSVs, optionally replacing the originals."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import os
from pathlib import Path
import tempfile

DATA_DIRECTORY = Path(__file__).resolve().parent
CSV_FILES = (
    "prepared_urls.csv",
    "prepared_urls_with_domains.csv",
)
MAX_GITHUB_FILE_BYTES = 100_000_000
CHUNK_SIZE = 1024 * 1024


def _hash_stream(stream) -> tuple[str, int]:
    digest = hashlib.sha256()
    byte_count = 0
    while chunk := stream.read(CHUNK_SIZE):
        digest.update(chunk)
        byte_count += len(chunk)
    return digest.hexdigest(), byte_count


def compress_csv(source: Path, replace_original: bool = False) -> tuple[Path, int]:
    if not source.is_file():
        raise FileNotFoundError(f"Prepared CSV not found: {source}")

    destination = source.with_name(f"{source.name}.gz")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=source.parent,
    )
    temporary_path = Path(temporary_name)
    original_digest = hashlib.sha256()
    original_size = 0

    try:
        with source.open("rb") as original, os.fdopen(descriptor, "wb") as target:
            with gzip.GzipFile(
                filename="",
                fileobj=target,
                mode="wb",
                compresslevel=6,
                mtime=0,
            ) as compressed:
                while chunk := original.read(CHUNK_SIZE):
                    original_digest.update(chunk)
                    original_size += len(chunk)
                    compressed.write(chunk)

        compressed_digest, decompressed_size = _hash_gzip(temporary_path)
        if (
            decompressed_size != original_size
            or compressed_digest != original_digest.hexdigest()
        ):
            raise OSError(f"Gzip verification failed for {source.name}.")

        compressed_size = temporary_path.stat().st_size
        if compressed_size >= MAX_GITHUB_FILE_BYTES:
            raise ValueError(
                f"{destination.name} is {compressed_size:,} bytes; "
                f"it must be below {MAX_GITHUB_FILE_BYTES:,} bytes."
            )

        os.chmod(temporary_path, source.stat().st_mode & 0o777)
        os.replace(temporary_path, destination)
        if replace_original:
            source.unlink()
        return destination, compressed_size
    finally:
        temporary_path.unlink(missing_ok=True)


def _hash_gzip(path: Path) -> tuple[str, int]:
    with gzip.open(path, "rb") as stream:
        return _hash_stream(stream)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Losslessly gzip prepared URL CSVs. Originals are preserved unless "
            "--replace-originals is specified."
        )
    )
    parser.add_argument(
        "--replace-originals",
        action="store_true",
        help="Delete each uncompressed CSV only after its gzip copy is verified.",
    )
    args = parser.parse_args()

    for filename in CSV_FILES:
        source = DATA_DIRECTORY / filename
        destination, compressed_size = compress_csv(
            source,
            replace_original=args.replace_originals,
        )
        print(f"{destination.name}: {compressed_size:,} bytes")


if __name__ == "__main__":
    main()
