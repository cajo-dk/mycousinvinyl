"""
ActiveMQ message publisher implementation.
"""

import json
import logging
from typing import Dict, Any
from stomp import Connection

from app.application.ports.message_publisher import MessagePublisher
from app.config import get_settings

logger = logging.getLogger(__name__)


class StompMessagePublisher(MessagePublisher):
    """STOMP protocol implementation for ActiveMQ."""

    def __init__(self):
        self.settings = get_settings()
        self.connection = None
        self._connect()

    def _connect(self):
        """Establish connection to ActiveMQ."""
        # Parse ActiveMQ URL (format: stomp://host:port)
        url = self.settings.activemq_url.replace("stomp://", "")
        host, port = url.split(":")

        self.connection = Connection([(host, int(port))])
        self.connection.connect(wait=True)
        logger.info(f"Connected to ActiveMQ at {host}:{port}")

    async def publish(
        self,
        destination: str,
        message: Dict[str, Any],
        headers: Dict[str, str] = None,
    ) -> None:
        """Publish a message to ActiveMQ."""
        if not self.connection or not self.connection.is_connected():
            self._connect()

        message_headers = headers or {}
        message_headers["content-type"] = "application/json"

        message_body = json.dumps(message)

        self.connection.send(
            destination=destination,
            body=message_body,
            headers=message_headers,
        )

        logger.info(f"Published message to {destination}: {message_body}")

    def disconnect(self):
        """Disconnect from ActiveMQ."""
        if self.connection and self.connection.is_connected():
            self.connection.disconnect()
            logger.info("Disconnected from ActiveMQ")
