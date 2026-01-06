"""
Factory for message publishers based on configured broker.
"""

from app.config import get_settings
from app.adapters.activemq.publisher import StompMessagePublisher
from app.adapters.mqtt.publisher import MqttMessagePublisher


def get_message_publisher():
    """Return a message publisher matching the configured broker."""
    settings = get_settings()
    broker = (settings.message_broker or "activemq").lower()

    if broker == "mqtt":
        return MqttMessagePublisher()

    return StompMessagePublisher()
