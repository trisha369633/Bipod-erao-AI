"""Split prepared URL datasets into training-ready CSV parts below a size limit."""

from __future__ import annotations

import argparse
import csv
import io
import os
from pathlib import Path
import re
import tempfile

import pandas as pd

DATA_DIRECTORY = (
    Path(__file__).resolve().parent / "dataset" / "url" / "prepared_mendeley"
)
DATASETS = {
    "prepared_urls": ("record_id", "normalized_url", "label", "source"),
    "prepared_urls_with_domains": (
        "record_id",
        "normalized_url",
        "label",
        "source",
        "registrable_domain",
    ),
}
DEFAULT_MAX_PART_BYTES = 15_000_000
DEFAULT_CHUNK_ROWS = 20_000
PART_PATTERN = re.compile(r"^(?P<stem>.+)_part_(?P<number>\d{3,})\.csv$")


def _positive_int(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def _find_source(directory: Path, stem: str) -> Path:
    for candidate in (directory / f"{stem}.csv", directory / f"{stem}.csv.gz"):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        f"Missing {stem}.csv or {stem}.csv.gz in {directory}"
    )


def _source_columns(source: Path) -> list[str]:
    header = pd.read_csv(
        source,
        nrows=0,
        encoding="utf-8-sig",
        compression="infer",
    )
    return list(header.columns)


def _column_mapping(columns: list[str], required: tuple[str, ...]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for name in required:
        # pandas adds ".1" to duplicate headers; DictReader uses the last value.
        duplicate_name = f"{name}.1"
        selected = duplicate_name if duplicate_name in columns else name
        if selected not in columns:
            raise ValueError(
                f"Required column {name!r} is missing from the input CSV."
            )
        mapping[name] = selected
    return mapping


def _csv_bytes(row: tuple[object, ...]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    values = [
        value if isinstance(value, str) else "" if pd.isna(value) else str(value)
        for value in row
    ]
    writer.writerow(values)
    return buffer.getvalue().encode("utf-8")


def _stage_parts(
    source: Path,
    stem: str,
    required: tuple[str, ...],
    stage_directory: Path,
    max_part_bytes: int,
    chunk_rows: int,
    keep_all_columns: bool,
) -> tuple[list[Path], int]:
    source_names = _source_columns(source)
    mapping = _column_mapping(source_names, required)
    if keep_all_columns:
        # Keep the enriched value, not the earlier blank duplicate column.
        use_columns = list(source_names)
        output_columns = list(source_names)
        for output_name, source_name in mapping.items():
            if source_name != output_name and output_name in use_columns:
                use_columns.remove(output_name)
                output_columns.remove(output_name)
                output_columns[output_columns.index(source_name)] = output_name
        if len(set(output_columns)) != len(output_columns):
            raise ValueError("Input contains duplicate columns that cannot be resolved.")
        rename_columns = {
            source_name: output_name
            for output_name, source_name in mapping.items()
            if source_name != output_name
        }
    else:
        use_columns = list(dict.fromkeys(mapping.values()))
        output_columns = list(required)
        rename_columns = {
            source_name: output_name
            for output_name, source_name in mapping.items()
            if source_name != output_name
        }

    header_size = len(_csv_bytes(tuple(output_columns)))
    if header_size >= max_part_bytes:
        raise ValueError("The CSV header alone exceeds the configured part size.")

    staged_parts: list[Path] = []
    current_stream: io.BufferedWriter | None = None
    current_size = 0
    total_rows = 0

    def close_part() -> None:
        nonlocal current_stream
        if current_stream is not None:
            current_stream.close()
            current_stream = None

    def start_part() -> None:
        nonlocal current_stream, current_size
        part_number = len(staged_parts) + 1
        part_path = stage_directory / f"{stem}_part_{part_number:03}.csv"
        current_stream = part_path.open("wb")
        header_bytes = _csv_bytes(tuple(output_columns))
        current_stream.write(header_bytes)
        current_size = len(header_bytes)
        staged_parts.append(part_path)

    try:
        chunks = pd.read_csv(
            source,
            chunksize=chunk_rows,
            dtype=str,
            keep_default_na=False,
            skip_blank_lines=False,
            encoding="utf-8-sig",
            compression="infer",
            usecols=use_columns,
        )
        for chunk in chunks:
            if rename_columns:
                chunk = chunk.rename(columns=rename_columns)
            chunk = chunk.loc[:, output_columns]
            for row in chunk.itertuples(index=False, name=None):
                row_bytes = _csv_bytes(row)
                if len(row_bytes) + header_size > max_part_bytes:
                    raise ValueError(
                        f"One row in {source.name} exceeds the configured "
                        f"{max_part_bytes:,}-byte part size."
                    )
                if current_stream is None:
                    start_part()
                elif current_size + len(row_bytes) > max_part_bytes:
                    close_part()
                    start_part()
                assert current_stream is not None
                current_stream.write(row_bytes)
                current_size += len(row_bytes)
                total_rows += 1
        if current_stream is None:
            start_part()
    finally:
        close_part()

    for part in staged_parts:
        part_size = part.stat().st_size
        if part_size > max_part_bytes or part_size >= 100_000_000:
            raise OSError(
                f"Size verification failed: {part.name} is {part_size:,} bytes."
            )
    return staged_parts, total_rows


def _existing_parts(directory: Path, stem: str) -> list[Path]:
    existing: list[Path] = []
    for path in directory.glob(f"{stem}_part_*.csv"):
        match = PART_PATTERN.fullmatch(path.name)
        if match and match.group("stem") == stem:
            existing.append(path)
    return existing


def split_dataset(
    directory: Path,
    stem: str,
    max_part_bytes: int,
    chunk_rows: int,
    keep_all_columns: bool,
    overwrite: bool,
) -> tuple[int, int]:
    source = _find_source(directory, stem)
    existing = _existing_parts(directory, stem)
    if existing and not overwrite:
        raise FileExistsError(
            f"Output parts already exist for {stem}; pass --overwrite to replace them."
        )

    with tempfile.TemporaryDirectory(
        prefix=f".{stem}_parts_", dir=directory
    ) as temporary_directory:
        stage_path = Path(temporary_directory)
        required = DATASETS[stem]
        parts, row_count = _stage_parts(
            source,
            stem,
            required,
            stage_path,
            max_part_bytes,
            chunk_rows,
            keep_all_columns,
        )
        final_paths = [directory / part.name for part in parts]
        for staged_path, final_path in zip(parts, final_paths):
            os.replace(staged_path, final_path)

    if overwrite:
        retained = {path.name for path in final_paths}
        for old_path in existing:
            if old_path.name not in retained:
                old_path.unlink()
    return len(final_paths), row_count


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Create training-ready CSV parts from the prepared URL datasets. "
            "Inputs may be plain CSVs or gzip-compressed CSVs."
        )
    )
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        default=DATA_DIRECTORY,
        help=f"Directory containing the prepared datasets (default: {DATA_DIRECTORY}).",
    )
    parser.add_argument(
        "--max-part-bytes",
        type=_positive_int,
        default=DEFAULT_MAX_PART_BYTES,
        help=f"Maximum bytes per output part (default: {DEFAULT_MAX_PART_BYTES:,}).",
    )
    parser.add_argument(
        "--chunk-rows",
        type=_positive_int,
        default=DEFAULT_CHUNK_ROWS,
        help=f"Rows pandas reads at a time (default: {DEFAULT_CHUNK_ROWS:,}).",
    )
    parser.add_argument(
        "--keep-all-columns",
        action="store_true",
        help="Retain non-training metadata columns as well as required fields.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing output parts for these two datasets.",
    )
    args = parser.parse_args()

    if not args.dataset_dir.is_dir():
        parser.error(f"Dataset directory does not exist: {args.dataset_dir}")
    if args.max_part_bytes >= 100_000_000:
        parser.error("--max-part-bytes must be strictly below 100,000,000.")

    for stem in DATASETS:
        part_count, row_count = split_dataset(
            args.dataset_dir,
            stem,
            args.max_part_bytes,
            args.chunk_rows,
            args.keep_all_columns,
            args.overwrite,
        )
        print(f"{stem}: {row_count:,} rows -> {part_count} CSV part(s)")


if __name__ == "__main__":
    main()
