"""
Activity websocket bridge worker.

Subscribes to broker activity topic and forwards messages to FastAPI.
"""

import json
import logging
import time
from uuid import uuid4
import httpx
from paho.mqtt import client as mqtt
from stomp import Connection
from stomp.listener import ConnectionListener

from app.config import get_settings
from app.adapters.mqtt.utils import parse_mqtt_url, mqtt_publish_topic

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ActivityBridgeListener(ConnectionListener):
    """Forward activity messages from the broker to the API websocket broadcaster."""

    def __init__(self):
        self.settings = get_settings()
        self.client = httpx.Client(timeout=5)

    def on_error(self, frame):
        logger.error(f"Broker error: {frame.body}")

    def on_message(self, frame):
        try:
            destination = frame.headers.get("destination")
            logger.info(f"Received activity message from {destination}")

            message = json.loads(frame.body)

            response = self.client.post(
                f"{self.settings.activity_bridge_url}/internal/activity",
                json=message,
                headers={"X-Activity-Token": self.settings.activity_bridge_token},
            )
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to forward activity message: {e}", exc_info=True)


def main():
    settings = get_settings()
    logger.info("Starting activity websocket bridge worker...")

    if not settings.activity_bridge_token:
        logger.error("ACTIVITY_BRIDGE_TOKEN is not configured; worker will not start.")
        return

    broker = (settings.message_broker or "activemq").lower()

    if broker == "mqtt":
        _run_mqtt_bridge(settings)
        return

    _run_stomp_bridge(settings)


def _run_stomp_bridge(settings) -> None:
    url = settings.activemq_url.replace("stomp://", "")
    host, port = url.split(":")

    conn = Connection([(host, int(port))])
    conn.set_listener("activity-bridge", ActivityBridgeListener())
    conn.connect(wait=True)

    conn.subscribe(destination=settings.activity_topic, id="activity-bridge-sub", ack="auto")

    logger.info("Activity bridge connected to ActiveMQ at %s:%s", host, port)
    logger.info("Subscribed to %s", settings.activity_topic)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down activity bridge...")
        conn.disconnect()


def _run_mqtt_bridge(settings) -> None:
    host, port, url_user, url_password = parse_mqtt_url(settings.mqtt_url)
    username = settings.mqtt_username or url_user
    password = settings.mqtt_password or url_password

    listener = ActivityBridgeListener()

    def on_connect(client, userdata, flags, rc):
        if rc != 0:
            logger.error("MQTT connection failed with code %s", rc)
            return
        mqtt_topic = mqtt_publish_topic(settings.activity_topic, settings.mqtt_topic_prefix)
        client.subscribe(mqtt_topic, qos=1)
        logger.info("Activity bridge connected to MQTT at %s:%s", host, port)
        logger.info("Subscribed to %s", mqtt_topic)

    def on_message(client, userdata, msg):
        try:
            frame = type("Frame", (), {"headers": {"destination": msg.topic}, "body": msg.payload.decode("utf-8")})
            listener.on_message(frame)
        except Exception:
            logger.exception("Failed to forward MQTT activity message")

    client = mqtt.Client(client_id=f"mycousinvinyl-activity-{uuid4().hex[:8]}")
    if username:
        client.username_pw_set(username=username, password=password or None)
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(host, port, keepalive=60)
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down activity bridge...")
        client.disconnect()


if __name__ == "__main__":
    main()
