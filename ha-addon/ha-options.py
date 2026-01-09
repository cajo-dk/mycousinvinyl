import json
import os
import shlex
from pathlib import Path


OPTION_KEYS = {
    "message_broker": "MESSAGE_BROKER",
    "environment": "ENVIRONMENT",
    "rbac_strict": "RBAC_STRICT",
    "health_check_token": "HEALTH_CHECK_TOKEN",
    "mqtt_url": "MQTT_URL",
    "mqtt_username": "MQTT_USERNAME",
    "mqtt_password": "MQTT_PASSWORD",
    "mqtt_topic_prefix": "MQTT_TOPIC_PREFIX",
    "activemq_url": "ACTIVEMQ_URL",
    "database_url": "DATABASE_URL",
    "activity_topic": "ACTIVITY_TOPIC",
    "activity_bridge_url": "ACTIVITY_BRIDGE_URL",
    "activity_bridge_token": "ACTIVITY_BRIDGE_TOKEN",
    "azure_tenant_id": "AZURE_TENANT_ID",
    "azure_client_id": "AZURE_CLIENT_ID",
    "azure_audience": "AZURE_AUDIENCE",
    "azure_group_admin": "AZURE_GROUP_ADMIN",
    "azure_group_editor": "AZURE_GROUP_EDITOR",
    "azure_group_viewer": "AZURE_GROUP_VIEWER",
    "discogs_service_url": "DISCOGS_SERVICE_URL",
    "discogs_user_agent": "DISCOGS_USER_AGENT",
    "discogs_key": "DISCOGS_KEY",
    "discogs_secret": "DISCOGS_SECRET",
    "discogs_oauth_token": "DISCOGS_OAUTH_TOKEN",
    "discogs_oauth_token_secret": "DISCOGS_OAUTH_TOKEN_SECRET",
    "album_wizard_api_url": "ALBUM_WIZARD_API_URL",
    "album_wizard_api_key": "ALBUM_WIZARD_API_KEY",
    "album_wizard_model_id": "ALBUM_WIZARD_MODEL_ID",
    "log_level": "LOG_LEVEL",
    "cors_allow_origins": "CORS_ALLOW_ORIGINS",
    "cors_allow_origin_regex": "CORS_ALLOW_ORIGIN_REGEX",
    "backup_schedule_days": "BACKUP_SCHEDULE_DAYS",
    "backup_schedule_time": "BACKUP_SCHEDULE_TIME",
    "backup_external_path": "BACKUP_EXTERNAL_PATH",
    "backup_sharepoint_site": "BACKUP_SHAREPOINT_SITE",
    "backup_sharepoint_library": "BACKUP_SHAREPOINT_LIBRARY",
    "backup_sharepoint_folder": "BACKUP_SHAREPOINT_FOLDER",
    "backup_sharepoint_tenant_id": "BACKUP_SHAREPOINT_TENANT_ID",
    "backup_sharepoint_client_id": "BACKUP_SHAREPOINT_CLIENT_ID",
    "backup_sharepoint_client_secret": "BACKUP_SHAREPOINT_CLIENT_SECRET",
    "backup_timezone": "BACKUP_TIMEZONE",
    "vite_api_url": "VITE_API_URL",
    "vite_azure_client_id": "VITE_AZURE_CLIENT_ID",
    "vite_azure_tenant_id": "VITE_AZURE_TENANT_ID",
    "vite_azure_redirect_uri": "VITE_AZURE_REDIRECT_URI",
    "vite_azure_group_admin": "VITE_AZURE_GROUP_ADMIN",
    "vite_debug_admin": "VITE_DEBUG_ADMIN",
    "vite_debug_nav": "VITE_DEBUG_NAV",
    "vite_manifest_env": "VITE_MANIFEST_ENV",
}


def _coerce_value(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    return str(value)


def main() -> None:
    options_path = Path("/data/options.json")
    if not options_path.exists():
        return

    options = json.loads(options_path.read_text())

    for key, env_key in OPTION_KEYS.items():
        if key not in options:
            continue
        value = _coerce_value(options[key])
        print(f"{env_key}={shlex.quote(value)}")


if __name__ == "__main__":
    main()
