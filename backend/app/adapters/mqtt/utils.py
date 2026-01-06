"""
MQTT helper utilities.
"""

from urllib.parse import urlparse


def parse_mqtt_url(url: str) -> tuple[str, int, str | None, str | None]:
    """Parse MQTT URL into host, port, username, password."""
    if "://" not in url:
        url = f"mqtt://{url}"

    parsed = urlparse(url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 1883
    return host, port, parsed.username, parsed.password


def mqtt_publish_topic(destination: str, prefix: str) -> str:
    """Map internal destinations to MQTT topics."""
    cleaned_prefix = prefix.strip("/")
    raw = destination.lstrip("/")
    if cleaned_prefix and raw.startswith(f"{cleaned_prefix}/"):
        return raw
    if raw.startswith("topic/"):
        raw = raw[len("topic/"):]
    return f"{cleaned_prefix}/{raw}" if cleaned_prefix else raw


def mqtt_inbound_destination(topic: str, prefix: str) -> str:
    """Map MQTT topics back to internal destinations."""
    cleaned_prefix = prefix.strip("/")
    if cleaned_prefix and topic.startswith(f"{cleaned_prefix}/"):
        suffix = topic[len(cleaned_prefix) + 1:]
        return f"/topic/{suffix}"
    return f"/topic/{topic.lstrip('/')}"
