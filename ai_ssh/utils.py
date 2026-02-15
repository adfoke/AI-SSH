import re

IPV4_PATTERN = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
IPV6_PATTERN = re.compile(r"\b(?:[0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}\b")
DOMAIN_PATTERN = re.compile(r"\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b")


def redact_sensitive(text: str, alias: str) -> str:
    redacted = IPV4_PATTERN.sub(alias, text)
    redacted = IPV6_PATTERN.sub(alias, redacted)
    redacted = DOMAIN_PATTERN.sub(alias, redacted)
    return redacted


def find_host_alias(user_input: str, aliases: list[str]) -> str | None:
    for alias in aliases:
        if alias and alias in user_input:
            return alias
    return None
