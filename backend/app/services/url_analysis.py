"""Offline URL parsing and structural security checks."""

from __future__ import annotations

import ipaddress
import re
from urllib.parse import parse_qsl, urlsplit

URL_PATTERN = re.compile(
    r"""(?ix)
    (?P<url>
        (?:[a-z][a-z0-9+.-]*://|www\.)[^\s<>"']+
        |
        (?<![@\w.-])
        (?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}
        (?::\d+)?
        (?:/[^\s<>"']*)?
    )
    """
)

# These services reveal their target only after a redirect; their presence alone is not proof of abuse.
SHORTENER_HOSTS = {
    "bit.ly",
    "cutt.ly",
    "is.gd",
    "lnkd.in",
    "ow.ly",
    "rb.gy",
    "rebrand.ly",
    "shorturl.at",
    "t.co",
    "tinyurl.com",
}

BRAND_DOMAINS = {
    "amazon": ("amazon.com", "amazon.co.uk", "amazon.in"),
    "apple": ("apple.com",),
    "bankofamerica": ("bankofamerica.com",),
    "facebook": ("facebook.com",),
    "google": ("google.com",),
    "microsoft": ("microsoft.com",),
    "paypal": ("paypal.com",),
}

WHATSAPP_HOSTS = {"wa.me", "whatsapp.com", "www.whatsapp.com", "api.whatsapp.com"}

GENERAL_EXPLANATION = {
    "en": "Only the URL's structure was checked locally. Live reputation, page content, and destinations reached after redirects were not checked.",
    "bn": "শুধু URL-এর গঠন স্থানীয়ভাবে পরীক্ষা করা হয়েছে। লাইভ রেপুটেশন, পেজের বিষয়বস্তু এবং রিডাইরেক্টের পরের গন্তব্য পরীক্ষা করা হয়নি।",
}

GENERAL_ACTION = {
    "en": "Do not enter credentials or payment details. Verify the sender and destination through an independently found official channel.",
    "bn": "কোনো পরিচয়পত্র বা পেমেন্টের তথ্য দেবেন না। নিজে থেকে খুঁজে পাওয়া অফিসিয়াল মাধ্যমে প্রেরক ও গন্তব্য যাচাই করুন।",
}

MESSAGE_CONTEXT_NOTE = {
    "en": "The message claims to be from Bangladesh Bank and urgently requests a KYC/account update. Treat that identity and request as suspicious; this does not prove the URL itself is malicious.",
    "bn": "মেসেজটি বাংলাদেশ ব্যাংকের পরিচয় দাবি করে জরুরিভাবে KYC/অ্যাকাউন্ট আপডেট চাইছে। পরিচয় ও অনুরোধটিকে সন্দেহজনক হিসেবে দেখুন; এতে URL-টি নিজে ক্ষতিকর প্রমাণিত হয় না।",
}


def _trim_url_candidate(candidate: str) -> str:
    value = candidate.strip(" \t\r\n<>()[]{}\"'")
    value = value.rstrip(".,!?;:")
    while value.endswith(")") and value.count(")") > value.count("("):
        value = value[:-1]
    while value.endswith("]") and value.count("]") > value.count("["):
        value = value[:-1]
    return value


def extract_urls(message: str) -> list[str]:
    """Extract unique scheme-based, www, and bare-domain URL candidates."""
    urls: list[str] = []
    seen: set[str] = set()
    text = re.sub(r"\[([^\]]*)\]\(([^)\s]+)\)", r"\1 \2 ", message)
    for match in URL_PATTERN.finditer(text):
        candidate = _trim_url_candidate(match.group("url"))
        if candidate and candidate.casefold() not in seen:
            seen.add(candidate.casefold())
            urls.append(candidate)
    return urls


def _normalize_url(value: str) -> tuple[str | None, str | None, bool]:
    candidate = _trim_url_candidate(value)
    if not candidate or any(ord(char) < 32 or ord(char) == 127 for char in candidate):
        return None, None, False
    if "\\" in candidate:
        return None, None, False

    normalized = candidate if "://" in candidate else f"https://{candidate}"
    try:
        parsed = urlsplit(normalized)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError:
        return None, None, False

    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc or not hostname:
        return None, None, False
    if any(char.isspace() for char in hostname):
        return None, None, False

    try:
        canonical_host = hostname.rstrip(".").encode("idna").decode("ascii").lower()
    except UnicodeError:
        return None, None, False
    if not canonical_host:
        return None, None, False

    has_userinfo = parsed.username is not None or parsed.password is not None
    host_for_url = f"[{canonical_host}]" if ":" in canonical_host else canonical_host
    if port is not None:
        host_for_url = f"{host_for_url}:{port}"
    normalized = parsed._replace(netloc=host_for_url, scheme=parsed.scheme.lower()).geturl()
    return normalized, canonical_host, has_userinfo


def _brand_impersonation(host: str) -> bool:
    labels = host.split(".")
    for brand, official_domains in BRAND_DOMAINS.items():
        if any(host == domain or host.endswith(f".{domain}") for domain in official_domains):
            continue
        if any(brand in label for label in labels):
            return True
    return False


def analyze_url(value: str) -> dict[str, object]:
    """Assess one URL without fetching it or consulting a live reputation service."""
    normalized_url, host, has_userinfo = _normalize_url(value)
    if normalized_url is None or host is None:
        return {
            "extracted_url": value,
            "normalized_url": None,
            "status": "unknown",
            "indicators": [],
            "explanation": {
                "en": "The URL is malformed or uses an unsupported format, so it could not be reliably analyzed.",
                "bn": "URL-টি ত্রুটিপূর্ণ বা অসমর্থিত ফরম্যাটের, তাই নির্ভরযোগ্যভাবে বিশ্লেষণ করা যায়নি।",
            },
            "recommended_action": GENERAL_ACTION,
        }

    parsed = urlsplit(normalized_url)
    indicators: list[str] = []
    suspicious = False

    def add_indicator(code: str, is_suspicious: bool = False) -> None:
        nonlocal suspicious
        if code not in indicators:
            indicators.append(code)
        suspicious = suspicious or is_suspicious

    if parsed.scheme == "http":
        add_indicator("http")

    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        add_indicator("ip_address", is_suspicious=True)

    if host in SHORTENER_HOSTS:
        add_indicator("shortener")

    if parsed.port not in (None, 80, 443):
        add_indicator("unusual_port", is_suspicious=True)

    if has_userinfo:
        add_indicator("userinfo", is_suspicious=True)

    if _brand_impersonation(host):
        add_indicator("brand_impersonation", is_suspicious=True)

    labels = host.split(".")
    auth_words = {"account", "bank", "login", "secure", "signin", "verify"}
    auth_labels = auth_words.intersection(re.split(r"[-.]", host))
    if "-" in host and len(auth_labels) >= 2:
        add_indicator("suspicious_hostname", is_suspicious=True)
    if len(labels) >= 4 and auth_words.intersection(labels[:-2]):
        recognized_brand_domain = any(
            host == domain or host.endswith(f".{domain}")
            for domains in BRAND_DOMAINS.values()
            for domain in domains
        )
        if not recognized_brand_domain:
            add_indicator("misleading_subdomain", is_suspicious=True)
    if len(labels) > 5:
        add_indicator("excessive_subdomains", is_suspicious=True)

    redirect_keys = {"continue", "dest", "next", "redirect", "redirect_uri", "return", "target", "url"}
    for key, target in parse_qsl(parsed.query):
        if key.casefold() not in redirect_keys:
            continue
        destination = urlsplit(target)
        if (
            destination.scheme.lower() in {"http", "https"}
            and destination.hostname
            and destination.hostname.casefold() != host
        ):
            add_indicator("external_redirect", is_suspicious=True)
            break

    recognized_whatsapp = host in WHATSAPP_HOSTS
    if recognized_whatsapp:
        add_indicator("whatsapp")

    if suspicious:
        status = "suspicious"
    elif recognized_whatsapp:
        status = "no_obvious_threat"
    else:
        status = "unknown"

    return {
        "extracted_url": value,
        "normalized_url": normalized_url,
        "status": status,
        "indicators": indicators,
        "explanation": GENERAL_EXPLANATION,
        "recommended_action": GENERAL_ACTION,
    }


def _message_context(message: str) -> dict[str, str] | None:
    claims_bank = re.search(
        r"(?:bangladesh\s+bank|বাংলাদেশ\s+ব্যাংক)", message, re.IGNORECASE
    )
    urgent = re.search(
        r"(?:urgent|immediately|right away|অবিলম্বে|জরুরি|এখনই)", message, re.IGNORECASE
    )
    requests_kyc = re.search(
        r"(?:\bkyc\b|account.{0,30}(?:update|verify|active)|"
        r"অ্যাকাউন্ট.{0,30}(?:সচল|আপডেট|যাচাই)|আপডেট)", message, re.IGNORECASE
    )
    if claims_bank and urgent and requests_kyc:
        return MESSAGE_CONTEXT_NOTE
    return None


def analyze_submitted_text(text: str) -> dict[str, object]:
    """Extract and analyze each URL in a message or URL-check request."""
    return {
        "urls": [analyze_url(url) for url in extract_urls(text)],
        "live_reputation_available": False,
        "live_reputation_message": {
            "en": "Live URL reputation checking is not configured. No live security scan was performed.",
            "bn": "লাইভ URL রেপুটেশন পরীক্ষা কনফিগার করা নেই। কোনো লাইভ নিরাপত্তা স্ক্যান করা হয়নি।",
        },
        "message_context": _message_context(text),
    }
