"""
Message broker consumer (worker).

This worker:
- Listens to integration events from the configured broker
- Executes application use-cases
- Does NOT perform authorization (only processes trusted internal events)
"""

import json
import logging
import time
import asyncio
import httpx
from uuid import UUID, uuid4

from paho.mqtt import client as mqtt
from stomp import Connection
from stomp.listener import ConnectionListener

from app.config import get_settings
from app.adapters.postgres.database import AsyncSessionLocal
from app.adapters.postgres.unit_of_work import SqlAlchemyUnitOfWork
from app.adapters.messaging.publisher_factory import get_message_publisher
from app.adapters.mqtt.utils import parse_mqtt_url, mqtt_inbound_destination, mqtt_publish_topic
from app.adapters.http.discogs_client import DiscogsClientAdapter
from app.application.services.discogs_service import DiscogsService
from app.application.services.pressing_service import PressingService
from app.domain.value_objects import VinylFormat, VinylSpeed, VinylSize
from app.domain.events import ActivityEvent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MessageHandler(ConnectionListener):
    """Handler for incoming broker messages."""

    def __init__(self):
        self.settings = get_settings()
        self.publisher = get_message_publisher()

    def on_error(self, frame):
        """Handle connection errors."""
        logger.error(f"Broker error: {frame.body}")

    def on_message(self, frame):
        """Handle incoming STOMP messages."""
        self.process_message(frame.headers.get("destination"), frame.body)

    def process_message(self, destination: str | None, body: str) -> None:
        """Handle incoming messages by destination/topic."""
        try:
            logger.info("Received message from %s", destination)
            logger.info("Message body: %s", body)

            message = json.loads(body)

            if destination == '/topic/artist.created':
                self._handle_artist_created(message)
            elif destination == '/topic/artist.updated':
                self._handle_artist_updated(message)
            elif destination == '/topic/artist.deleted':
                self._handle_artist_deleted(message)
            elif destination == '/topic/album.created':
                self._handle_album_created(message)
            elif destination == '/topic/pressing.created':
                self._handle_pressing_created(message)
            elif destination == '/topic/pressing.master.import':
                self._handle_pressing_master_import(message)
            elif destination == '/topic/collection.item.added':
                self._handle_collection_item_added(message)
            else:
                logger.warning("No handler for destination: %s", destination)

        except Exception as e:
            logger.error("Error processing message: %s", e, exc_info=True)

    def _handle_artist_created(self, message):
        """Handle artist.created event."""
        logger.info(f"Artist created: {message.get('name')} (ID: {message.get('artist_id')})")
        # Potential use cases:
        # - Send notifications to administrators
        # - Update search indexes
        # - Trigger data enrichment workflows
        # - Update analytics/metrics

    def _handle_artist_updated(self, message):
        """Handle artist.updated event."""
        logger.info(f"Artist updated: {message.get('artist_id')}, fields: {message.get('updated_fields', {})}")
        # Potential use cases:
        # - Invalidate caches
        # - Update search indexes
        # - Send change notifications

    def _handle_artist_deleted(self, message):
        """Handle artist.deleted event."""
        logger.info(f"Artist deleted: {message.get('artist_id')}")
        # Potential use cases:
        # - Remove from search indexes
        # - Clean up related data
        # - Send deletion notifications

    def _handle_album_created(self, message):
        """Handle album.created event."""
        logger.info(f"Album created: {message.get('title')} (ID: {message.get('album_id')})")
        # Placeholder for future business logic

    def _handle_pressing_created(self, message):
        """Handle pressing.created event."""
        logger.info(f"Pressing created: {message.get('pressing_id')}")
        # Placeholder for future business logic

    def _handle_pressing_master_import(self, message):
        """Handle pressing master import request."""
        logger.info("Pressing master import requested: %s", message.get("discogs_master_id"))
        try:
            asyncio.run(self._import_pressing_master(message))
        except Exception:
            logger.exception("Failed to process pressing master import")

    async def _import_pressing_master(self, message):
        pressing_id = message.get("pressing_id")
        discogs_master_id = message.get("discogs_master_id")
        created_by = message.get("created_by")
        if not pressing_id or not discogs_master_id:
            logger.error("Missing pressing_id or discogs_master_id in message payload")
            return

        try:
            pressing_uuid = UUID(pressing_id)
        except ValueError:
            logger.error("Invalid pressing_id in message payload: %s", pressing_id)
            return

        created_by_uuid = None
        if created_by:
            try:
                created_by_uuid = UUID(created_by)
            except ValueError:
                logger.warning("Invalid created_by in message payload: %s", created_by)

        settings = get_settings()
        discogs_service = DiscogsService(DiscogsClientAdapter(settings.discogs_service_url))

        async with SqlAlchemyUnitOfWork(AsyncSessionLocal()) as uow:
            master_pressing = await uow.pressing_repository.get(pressing_uuid)
            if not master_pressing:
                logger.error("Pressing %s not found for master import", pressing_id)
                return
            if master_pressing.master_id:
                logger.error("Pressing %s already belongs to a master; aborting import", pressing_id)
                return
            album_id = master_pressing.album_id
            album = await uow.album_repository.get(album_id)
            album_title = album.title if album else "Unknown album"

        releases = await discogs_service.get_master_releases(int(discogs_master_id), limit=100)
        created_count = 0

        for release in releases:
            if release.get("type") != "release":
                continue
            release_id = release.get("id")
            if not release_id:
                continue

            async with SqlAlchemyUnitOfWork(AsyncSessionLocal()) as uow:
                existing = await uow.pressing_repository.get_by_discogs_release_id(int(release_id))
                if existing:
                    continue

                try:
                    details = await discogs_service.get_release(int(release_id))
                except httpx.HTTPStatusError as exc:
                    status_code = exc.response.status_code if exc.response is not None else None
                    if status_code == 429:
                        logger.warning("Discogs rate limit hit for release %s; retrying", release_id)
                        await asyncio.sleep(2)
                        try:
                            details = await discogs_service.get_release(int(release_id))
                        except Exception:
                            logger.warning("Skipping release %s after retry failure", release_id)
                            continue
                    else:
                        logger.warning("Skipping release %s due to Discogs error", release_id)
                        continue
                except Exception:
                    logger.warning("Skipping release %s due to Discogs error", release_id)
                    continue
                format_value = _map_discogs_format(details)
                speed_value = _map_discogs_speed(details)
                size_value = _map_discogs_size(details)
                disc_count = details.get("disc_count") or 1
                year_value = details.get("year")
                edition_type = details.get("edition_type") or "Standard"

                existing_edition = await uow.lookup_repository.get_edition_type(edition_type)
                if not existing_edition:
                    await uow.lookup_repository.create_edition_type(
                        code=edition_type,
                        name=edition_type,
                    )

                service = PressingService(uow)
                await service.create_pressing(
                    album_id=album_id,
                    format=format_value,
                    speed_rpm=speed_value,
                    size_inches=size_value,
                    disc_count=disc_count,
                    pressing_country=details.get("country"),
                    pressing_year=year_value,
                    pressing_plant=details.get("pressing_plant"),
                    mastering_engineer=details.get("mastering_engineer"),
                    mastering_studio=details.get("mastering_studio"),
                    vinyl_color=details.get("vinyl_color") or "Black",
                    label_design=details.get("label"),
                    edition_type=details.get("edition_type"),
                    barcode=details.get("identifiers") or details.get("barcode"),
                    image_url=details.get("image_url"),
                    discogs_release_id=int(release_id),
                    discogs_master_id=int(discogs_master_id),
                    master_id=pressing_uuid,
                    created_by=created_by_uuid,
                )
                created_count += 1

        logger.info("Master import complete: %s pressings created", created_count)

        activity_event = ActivityEvent(
            operation="imported",
            entity_type="pressing_import",
            summary=f"{created_count} pressings for album {album_title}",
            user_id=created_by_uuid,
        )
        await self.publisher.publish(
            self.settings.activity_topic,
            activity_event.to_dict(),
        )


def _collect_discogs_tokens(details: dict) -> str:
    values = []
    for key in ("formats", "format_descriptions"):
        entry = details.get(key) or []
        if isinstance(entry, list):
            values.extend(entry)
    return " ".join([str(value).lower() for value in values])


def _map_discogs_format(details: dict) -> VinylFormat:
    tokens = _collect_discogs_tokens(details)
    if "ep" in tokens:
        return VinylFormat.EP
    if "single" in tokens:
        return VinylFormat.SINGLE
    if "maxi" in tokens:
        return VinylFormat.MAXI
    return VinylFormat.LP


def _map_discogs_speed(details: dict) -> VinylSpeed:
    tokens = _collect_discogs_tokens(details)
    if "78" in tokens:
        return VinylSpeed.RPM_78
    if "45" in tokens:
        return VinylSpeed.RPM_45
    return VinylSpeed.RPM_33


def _map_discogs_size(details: dict) -> VinylSize:
    tokens = _collect_discogs_tokens(details)
    if '7"' in tokens:
        return VinylSize.SIZE_7
    if '10"' in tokens:
        return VinylSize.SIZE_10
    return VinylSize.SIZE_12

    def _handle_collection_item_added(self, message):
        """Handle collection.item.added event."""
        logger.info(f"Collection item added for user {message.get('user_id')}")
        # Potential use cases:
        # - Update user statistics
        # - Send achievement notifications
        # - Update recommendations engine


def main():
    """Start the worker consumer."""
    settings = get_settings()
    logger.info("Starting worker consumer...")
    broker = (settings.message_broker or "activemq").lower()

    if broker == "mqtt":
        _run_mqtt_consumer(settings)
        return

    _run_stomp_consumer(settings)


def _run_stomp_consumer(settings) -> None:
    url = settings.activemq_url.replace("stomp://", "")
    host, port = url.split(":")

    conn = Connection([(host, int(port))])
    conn.set_listener('message-handler', MessageHandler())
    conn.connect(wait=True)

    conn.subscribe(destination='/topic/artist.created', id='artist-created-sub', ack='auto')
    conn.subscribe(destination='/topic/artist.updated', id='artist-updated-sub', ack='auto')
    conn.subscribe(destination='/topic/artist.deleted', id='artist-deleted-sub', ack='auto')
    conn.subscribe(destination='/topic/album.created', id='album-created-sub', ack='auto')
    conn.subscribe(destination='/topic/pressing.created', id='pressing-created-sub', ack='auto')
    conn.subscribe(destination='/topic/pressing.master.import', id='pressing-master-import-sub', ack='auto')
    conn.subscribe(destination='/topic/collection.item.added', id='collection-item-added-sub', ack='auto')

    logger.info("Worker connected to ActiveMQ at %s:%s", host, port)
    logger.info("Listening for messages...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down worker...")
        conn.disconnect()


def _run_mqtt_consumer(settings) -> None:
    host, port, url_user, url_password = parse_mqtt_url(settings.mqtt_url)
    username = settings.mqtt_username or url_user
    password = settings.mqtt_password or url_password

    handler = MessageHandler()

    def on_connect(client, userdata, flags, rc):
        if rc != 0:
            logger.error("MQTT connection failed with code %s", rc)
            return
        client.subscribe(mqtt_publish_topic('/topic/artist.created', settings.mqtt_topic_prefix), qos=1)
        client.subscribe(mqtt_publish_topic('/topic/artist.updated', settings.mqtt_topic_prefix), qos=1)
        client.subscribe(mqtt_publish_topic('/topic/artist.deleted', settings.mqtt_topic_prefix), qos=1)
        client.subscribe(mqtt_publish_topic('/topic/album.created', settings.mqtt_topic_prefix), qos=1)
        client.subscribe(mqtt_publish_topic('/topic/pressing.created', settings.mqtt_topic_prefix), qos=1)
        client.subscribe(mqtt_publish_topic('/topic/pressing.master.import', settings.mqtt_topic_prefix), qos=1)
        client.subscribe(mqtt_publish_topic('/topic/collection.item.added', settings.mqtt_topic_prefix), qos=1)
        logger.info("Worker connected to MQTT at %s:%s", host, port)
        logger.info("Listening for messages...")

    def on_message(client, userdata, msg):
        try:
            destination = mqtt_inbound_destination(msg.topic, settings.mqtt_topic_prefix)
            handler.process_message(destination, msg.payload.decode("utf-8"))
        except Exception:
            logger.exception("Failed to handle MQTT message on %s", msg.topic)

    client = mqtt.Client(client_id=f"mycousinvinyl-worker-{uuid4().hex[:8]}")
    if username:
        client.username_pw_set(username=username, password=password or None)
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(host, port, keepalive=60)
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down worker...")
        client.disconnect()


if __name__ == "__main__":
    main()
