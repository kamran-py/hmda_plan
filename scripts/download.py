from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from collections.abc import Iterable
from urllib import error, request

from scripts.config import ALL_YEARS, RAW_DIR, SMOKE_TEST_YEARS, get_user_agent, year_spec


FALLBACK_GET_BYTES = 4096
HEAD_FALLBACK_STATUS_CODES = {400, 403, 405, 406, 501}
DOWNLOAD_CHUNK_BYTES = 1024 * 1024
PROGRESS_INTERVAL_BYTES = 100 * 1024 * 1024
DEFAULT_MANIFEST_PATH = RAW_DIR / "download_manifest.json"


@dataclass(frozen=True)
class UrlValidationResult:
    year: int
    method: str
    status: int | None
    final_url: str
    content_type: str | None
    content_length: str | None
    bytes_read: int
    signature_hex: str | None = None
    signature_text: str | None = None
    content_check: str | None = None
    error: str | None = None


@dataclass
class DownloadResult:
    year: int
    source_url: str
    output_path: str
    status: str
    content_length: int | None
    downloaded_bytes: int
    started_at: str
    finished_at: str
    error: str | None = None


def iter_years(smoke: bool) -> Iterable[int]:
    return SMOKE_TEST_YEARS if smoke else ALL_YEARS


def build_download_plan(years: Iterable[int]) -> list[str]:
    lines = [
        "Download plan only. Phase 1 does not perform network requests.",
        f"User-Agent for later approved downloads: {get_user_agent()}",
    ]
    for year in years:
        spec = year_spec(year)
        lines.append(f"{year}: {spec.url}")
        lines.append(f"  target: {spec.raw_path}")
        lines.append("  resume strategy: write .partial file, then atomically rename after completion")
    return lines


def _request_headers(user_agent: str, *, use_range: bool = False) -> dict[str, str]:
    headers = {
        "User-Agent": user_agent,
        "Accept-Encoding": "identity",
        "Connection": "close",
    }
    if use_range:
        headers["Range"] = f"bytes=0-{FALLBACK_GET_BYTES - 1}"
    return headers


def _download_headers(user_agent: str, start_byte: int = 0) -> dict[str, str]:
    headers = {
        "User-Agent": user_agent,
        "Accept-Encoding": "identity",
        "Connection": "close",
    }
    if start_byte > 0:
        headers["Range"] = f"bytes={start_byte}-"
    return headers


def _now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _parse_total_size(response) -> int | None:
    content_range = response.headers.get("Content-Range")
    if content_range:
        match = re.search(r"/(\d+)$", content_range)
        if match:
            return int(match.group(1))

    content_length = response.headers.get("Content-Length")
    if content_length and content_length.isdigit():
        return int(content_length)
    return None


def _partial_path(output_path: Path) -> Path:
    return output_path.with_name(f"{output_path.name}.partial")


def _format_bytes(value: int | None) -> str:
    if value is None:
        return "unknown"
    gib = value / (1024**3)
    if gib >= 1:
        return f"{gib:.2f} GiB"
    mib = value / (1024**2)
    return f"{mib:.2f} MiB"


def check_disk_space(min_free_gb: float) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    usage = shutil.disk_usage(RAW_DIR)
    free_gb = usage.free / (1024**3)
    print(f"Disk preflight: {free_gb:.2f} GiB free in {RAW_DIR}")
    if free_gb < min_free_gb:
        raise RuntimeError(f"Insufficient free disk space: {free_gb:.2f} GiB available, {min_free_gb:.2f} GiB required")


def write_manifest(path: Path, records: list[DownloadResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serializable = [record.__dict__ for record in records]
    with path.open("w", encoding="utf-8") as handle:
        json.dump(serializable, handle, indent=2)
        handle.write("\n")


def _result_from_response(year: int, method: str, response, bytes_read: int = 0) -> UrlValidationResult:
    return UrlValidationResult(
        year=year,
        method=method,
        status=response.status,
        final_url=response.geturl(),
        content_type=response.headers.get("Content-Type"),
        content_length=response.headers.get("Content-Length"),
        bytes_read=bytes_read,
    )


def _content_check_for_bytes(year: int, chunk: bytes) -> str:
    spec = year_spec(year)
    if spec.raw_path.suffix == ".zip":
        zip_headers = (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")
        return "zip_header_ok" if chunk.startswith(zip_headers) else "zip_header_unexpected"

    decoded = chunk[:512].decode("utf-8", errors="replace")
    printable_chars = sum(1 for char in decoded if char.isprintable() or char in "\r\n\t")
    printable_ratio = printable_chars / max(len(decoded), 1)
    looks_delimited = "," in decoded and ("\n" in decoded or "\r" in decoded)
    if printable_ratio > 0.85 and looks_delimited:
        return "text_csv_like"
    if printable_ratio > 0.85:
        return "text_like"
    return "text_csv_unexpected"


def _signature_text(chunk: bytes) -> str:
    return chunk[:80].decode("utf-8", errors="replace").replace("\r", "\\r").replace("\n", "\\n")


def _result_from_http_error(year: int, method: str, exc: error.HTTPError) -> UrlValidationResult:
    return UrlValidationResult(
        year=year,
        method=method,
        status=exc.code,
        final_url=exc.geturl(),
        content_type=exc.headers.get("Content-Type"),
        content_length=exc.headers.get("Content-Length"),
        bytes_read=0,
        error=str(exc),
    )


def validate_url(year: int, timeout_seconds: int = 30) -> UrlValidationResult:
    spec = year_spec(year)
    user_agent = get_user_agent()
    head_request = request.Request(
        spec.url,
        headers=_request_headers(user_agent),
        method="HEAD",
    )

    try:
        with request.urlopen(head_request, timeout=timeout_seconds) as response:
            return _result_from_response(year, "HEAD", response)
    except error.HTTPError as exc:
        if exc.code not in HEAD_FALLBACK_STATUS_CODES:
            return _result_from_http_error(year, "HEAD", exc)
    except error.URLError as exc:
        return UrlValidationResult(
            year=year,
            method="HEAD",
            status=None,
            final_url=spec.url,
            content_type=None,
            content_length=None,
            bytes_read=0,
            error=str(exc),
        )

    get_request = request.Request(
        spec.url,
        headers=_request_headers(user_agent, use_range=True),
        method="GET",
    )
    try:
        with request.urlopen(get_request, timeout=timeout_seconds) as response:
            chunk = response.read(FALLBACK_GET_BYTES)
            head = chunk[:16]
            return UrlValidationResult(
                year=year,
                method="GET",
                status=response.status,
                final_url=response.geturl(),
                content_type=response.headers.get("Content-Type"),
                content_length=response.headers.get("Content-Length"),
                bytes_read=len(chunk),
                signature_hex=head.hex(" "),
                signature_text=_signature_text(chunk),
                content_check=_content_check_for_bytes(year, chunk),
            )
    except error.HTTPError as exc:
        return _result_from_http_error(year, "GET", exc)
    except error.URLError as exc:
        return UrlValidationResult(
            year=year,
            method="GET",
            status=None,
            final_url=spec.url,
            content_type=None,
            content_length=None,
            bytes_read=0,
            error=str(exc),
        )


def format_validation_result(result: UrlValidationResult) -> list[str]:
    lines = [
        f"{result.year}:",
        f"  method: {result.method}",
        f"  status: {result.status if result.status is not None else 'unavailable'}",
        f"  final_url: {result.final_url}",
        f"  content_type: {result.content_type or 'unavailable'}",
        f"  content_length: {result.content_length or 'unavailable'}",
    ]
    if result.method == "GET":
        lines.append(f"  fallback_bytes_read: {result.bytes_read}")
        lines.append(f"  signature_hex: {result.signature_hex or 'unavailable'}")
        lines.append(f"  signature_text: {result.signature_text or 'unavailable'}")
        lines.append(f"  content_check: {result.content_check or 'unavailable'}")
    if result.error:
        lines.append(f"  error: {result.error}")
    return lines


def validate_urls(years: Iterable[int], timeout_seconds: int) -> int:
    exit_code = 0
    for year in years:
        result = validate_url(year, timeout_seconds=timeout_seconds)
        for line in format_validation_result(result):
            print(line)
        if result.status is None or result.status >= 400:
            exit_code = 1
    return exit_code


def download_year(
    year: int,
    *,
    force: bool,
    timeout_seconds: int,
    retries: int,
    backoff_seconds: float,
) -> DownloadResult:
    spec = year_spec(year)
    output_path = spec.raw_path
    partial_path = _partial_path(output_path)
    user_agent = get_user_agent()
    started_at = _now_iso()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists() and not force:
        print(f"{year}: skip existing {output_path}")
        return DownloadResult(
            year=year,
            source_url=spec.url,
            output_path=str(output_path),
            status="skipped_existing",
            content_length=output_path.stat().st_size,
            downloaded_bytes=output_path.stat().st_size,
            started_at=started_at,
            finished_at=_now_iso(),
        )

    if force:
        if output_path.exists():
            output_path.unlink()
        if partial_path.exists():
            partial_path.unlink()

    last_error: str | None = None
    content_length: int | None = None

    for attempt in range(1, retries + 1):
        existing_bytes = partial_path.stat().st_size if partial_path.exists() else 0
        mode = "ab" if existing_bytes else "wb"
        headers = _download_headers(user_agent, start_byte=existing_bytes)
        req = request.Request(spec.url, headers=headers, method="GET")

        try:
            print(f"{year}: attempt {attempt}/{retries}; starting at byte {existing_bytes}; target {output_path.name}")
            with request.urlopen(req, timeout=timeout_seconds) as response:
                if existing_bytes > 0 and response.status == 200:
                    print(f"{year}: server ignored Range request; restarting partial file")
                    existing_bytes = 0
                    mode = "wb"

                content_length = _parse_total_size(response)
                if response.status not in {200, 206}:
                    raise RuntimeError(f"Unexpected HTTP status {response.status}")

                total_written = existing_bytes
                next_progress = total_written + PROGRESS_INTERVAL_BYTES
                with partial_path.open(mode + "") as handle:
                    while True:
                        chunk = response.read(DOWNLOAD_CHUNK_BYTES)
                        if not chunk:
                            break
                        handle.write(chunk)
                        total_written += len(chunk)
                        if total_written >= next_progress:
                            print(f"{year}: downloaded {_format_bytes(total_written)} of {_format_bytes(content_length)}")
                            sys.stdout.flush()
                            next_progress = total_written + PROGRESS_INTERVAL_BYTES

            partial_path.replace(output_path)
            downloaded_bytes = output_path.stat().st_size
            print(f"{year}: complete {output_path} ({_format_bytes(downloaded_bytes)})")
            return DownloadResult(
                year=year,
                source_url=spec.url,
                output_path=str(output_path),
                status="downloaded",
                content_length=content_length,
                downloaded_bytes=downloaded_bytes,
                started_at=started_at,
                finished_at=_now_iso(),
            )
        except (OSError, error.URLError, error.HTTPError, RuntimeError) as exc:
            last_error = str(exc)
            print(f"{year}: attempt {attempt}/{retries} failed: {last_error}")
            if attempt < retries:
                sleep_seconds = backoff_seconds * (2 ** (attempt - 1))
                print(f"{year}: retrying in {sleep_seconds:.1f}s")
                time.sleep(sleep_seconds)

    downloaded_bytes = partial_path.stat().st_size if partial_path.exists() else 0
    return DownloadResult(
        year=year,
        source_url=spec.url,
        output_path=str(output_path),
        status="failed",
        content_length=content_length,
        downloaded_bytes=downloaded_bytes,
        started_at=started_at,
        finished_at=_now_iso(),
        error=last_error,
    )


def download_years(
    years: Iterable[int],
    *,
    force: bool,
    timeout_seconds: int,
    retries: int,
    backoff_seconds: float,
    min_free_gb: float,
    manifest_path: Path,
) -> int:
    check_disk_space(min_free_gb)
    records: list[DownloadResult] = []
    exit_code = 0
    year_list = list(years)
    print(f"Starting raw HMDA downloads for years: {', '.join(str(year) for year in year_list)}")
    print(f"Manifest: {manifest_path}")

    for year in year_list:
        result = download_year(
            year,
            force=force,
            timeout_seconds=timeout_seconds,
            retries=retries,
            backoff_seconds=backoff_seconds,
        )
        records.append(result)
        write_manifest(manifest_path, records)
        if result.status == "failed":
            exit_code = 1

    return exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan HMDA downloads or validate URLs.")
    parser.add_argument("--all-years", action="store_true", help="Show the full 2007-2024 download plan.")
    parser.add_argument("--years", nargs="*", type=int, help="Specific years to plan or validate.")
    parser.add_argument("--download", action="store_true", help="Download raw HMDA files.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing completed and partial files.")
    parser.add_argument(
        "--validate-urls",
        action="store_true",
        help="Make lightweight URL checks. Requires approval before running.",
    )
    parser.add_argument("--timeout-seconds", type=int, default=120)
    parser.add_argument("--retries", type=int, default=5)
    parser.add_argument("--backoff-seconds", type=float, default=5.0)
    parser.add_argument("--min-free-gb", type=float, default=100.0)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    args = parser.parse_args()

    years = args.years if args.years else list(iter_years(smoke=not args.all_years))
    if args.validate_urls:
        return validate_urls(years, timeout_seconds=args.timeout_seconds)

    if args.download:
        return download_years(
            years,
            force=args.force,
            timeout_seconds=args.timeout_seconds,
            retries=args.retries,
            backoff_seconds=args.backoff_seconds,
            min_free_gb=args.min_free_gb,
            manifest_path=args.manifest,
        )

    for line in build_download_plan(years):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
