from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration settings."""

    # Database
    database_url: str

    # Messaging
    message_broker: str = "activemq"

    # ActiveMQ
    activemq_url: str = "stomp://activemq:61613"
    activity_topic: str = "/topic/system.activity"
    activity_bridge_url: str = "http://api:8000"
    activity_bridge_token: str = ""

    # MQTT (Mosquitto)
    mqtt_url: str = "mqtt://mosquitto:1883"
    mqtt_username: str = ""
    mqtt_password: str = ""
    mqtt_topic_prefix: str = "mycousinvinyl"

    # Azure Entra ID
    azure_tenant_id: str
    azure_client_id: str
    azure_audience: str

    # Azure AD Group IDs for role-based access control
    # These should be configured in Azure Portal -> Entra ID -> Groups
    azure_group_admin: str = ""  # Full system access
    azure_group_editor: str = ""  # Can create/edit collections and catalog
    azure_group_viewer: str = ""  # Read-only access

    # Application
    log_level: str = "INFO"
    environment: str = "development"

    # API
    api_v1_prefix: str = "/api/v1"

    # Discogs microservice
    discogs_service_url: str = "http://discogs-service:8001"
    discogs_user_agent: str = "MyCousinVinyl/1.0"

    # Discogs OAuth (user collection)
    discogs_consumer_key: str = ""
    discogs_consumer_secret: str = ""
    discogs_oauth_callback_url: str = "http://localhost:8000/api/v1/discogs/oauth/callback"
    discogs_oauth_authorize_url: str = "https://www.discogs.com/oauth/authorize"
    discogs_oauth_api_base_url: str = "https://api.discogs.com"
    discogs_oauth_rate_limit_per_minute: int = 55
    discogs_import_log_level: str = "INFO"

    # Album Wizard AI
    album_wizard_api_url: str = ""
    album_wizard_api_key: str = ""
    album_wizard_timeout_seconds: float = 30.0
    album_wizard_model_id: str = ""

    # Frontend
    frontend_base_url: str = "https://ws01.cajo.dk"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
