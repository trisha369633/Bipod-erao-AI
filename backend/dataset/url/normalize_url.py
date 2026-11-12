"""Safe, offline URL normalization for the URL dataset staging pipeline."""

from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlsplit, urlunsplit


class URLNormalizationError(ValueError):
    """Raised when an input cannot be normalized as an absolute HTTP(S) URL."""


_SCHEME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def normalize_url(value: str) -> str:
    """Normalize URL scheme/host without fetching or classifying the URL.

    Requires an explicit HTTP(S) scheme to avoid guessing the transport.
    Paths, queries, and fragments are preserved; redirects are never followed.
    """
    if not isinstance(value, str) or not value:
        raise URLNormalizationError("URL must be a non-empty string.")
    if value != value.strip():
        raise URLNormalizationError("URL has leading or trailing whitespace.")
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise URLNormalizationError("URL contains control characters.")
    if any(char.isspace() for char in value) or "\\" in value:
        raise URLNormalizationError("URL contains whitespace or a backslash.")
    if not _SCHEME_PATTERN.match(value):
        raise URLNormalizationError("URL must include an explicit http:// or https:// scheme.")

    try:
        parsed = urlsplit(value)
        scheme = parsed.scheme.lower()
        hostname = parsed.hostname
        port = parsed.port
    except ValueError as exc:
        raise URLNormalizationError("URL authority or port is malformed.") from exc

    if scheme not in {"http", "https"}:
        raise URLNormalizationError("Only HTTP and HTTPS URLs are supported.")
    if not parsed.netloc or not hostname:
        raise URLNormalizationError("URL must include a hostname.")

    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        try:
            ascii_hostname = hostname.rstrip(".").encode("idna").decode("ascii").lower()
        except UnicodeError as exc:
            raise URLNormalizationError("Hostname cannot be converted to IDNA.") from exc

        labels = ascii_hostname.split(".")
        if (
            not ascii_hostname
            or len(ascii_hostname) > 253
            or any(
                not label
                or len(label) > 63
                or label.startswith("-")
                or label.endswith("-")
                or not re.fullmatch(r"[a-z0-9-]+", label)
                for label in labels
            )
        ):
            raise URLNormalizationError("Hostname syntax is malformed.")
        canonical_host = ascii_hostname
    else:
        canonical_host = address.compressed.lower()

    if port is not None and not 1 <= port <= 65535:
        raise URLNormalizationError("Port must be between 1 and 65535.")

    userinfo, separator, _ = parsed.netloc.rpartition("@")
    host_for_url = f"[{canonical_host}]" if ":" in canonical_host else canonical_host
    if port is not None and not (
        (scheme == "http" and port == 80)
        or (scheme == "https" and port == 443)
    ):
        host_for_url = f"{host_for_url}:{port}"
    netloc = f"{userinfo}@{host_for_url}" if separator else host_for_url

    return urlunsplit(
        (scheme, netloc, parsed.path, parsed.query, parsed.fragment)
    )


def hostname_from_url(value: str) -> str:
    """Return a canonical hostname from a valid absolute HTTP(S) URL."""
    normalized = normalize_url(value)
    hostname = urlsplit(normalized).hostname
    if hostname is None:
        raise URLNormalizationError("URL must include a hostname.")
    try:
        return ipaddress.ip_address(hostname).compressed.lower()
    except ValueError:
        return hostname.encode("idna").decode("ascii").lower()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="absolute HTTP(S) URL to normalize")
    args = parser.parse_args()
    try:
        print(normalize_url(args.url))
    except URLNormalizationError as exc:
        parser.error(str(exc))
