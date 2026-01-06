"""
MQTT message publisher implementation.
"""

import json
import logging
from typing import Dict, Any
from uuid import uuid4

from paho.mqtt import client as mqtt

from app.application.ports.message_publisher import MessagePublisher
from app.config import get_settings
from app.adapters.mqtt.utils import parse_mqtt_url, mqtt_publish_topic

logger = logging.getLogger(__name__)


class MqttMessagePublisher(MessagePublisher):
    """MQTT publisher for Mosquitto or compatible brokers."""

    def __init__(self):
        self.settings = get_settings()
        self.client = None
        self._connect()

    def _connect(self) -> None:
        host, port, url_user, url_password = parse_mqtt_url(self.settings.mqtt_url)
        username = self.settings.mqtt_username or url_user
        password = self.settings.mqtt_password or url_password

        client_id = f"mycousinvinyl-pub-{uuid4().hex[:8]}"
        self.client = mqtt.Client(client_id=client_id, clean_session=True)
        if username:
            self.client.username_pw_set(username=username, password=password or None)

        self.client.connect(host, port, keepalive=60)
        self.client.loop_start()
        logger.info("Connected to MQTT broker at %s:%s", host, port)

    async def publish(
        self,
        destination: str,
        message: Dict[str, Any],
        headers: Dict[str, str] = None,
    ) -> None:
        """Publish a message to MQTT."""
        if not self.client or not self.client.is_connected():
            self._connect()

        message_body = json.dumps(message)
        topic = mqtt_publish_topic(destination, self.settings.mqtt_topic_prefix)
        result = self.client.publish(topic, payload=message_body, qos=1)
        result.wait_for_publish()

        logger.info("Published message to %s: %s", topic, message_body)

    def disconnect(self) -> None:
        """Disconnect from MQTT broker."""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("Disconnected from MQTT broker")
