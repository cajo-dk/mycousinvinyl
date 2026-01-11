import logging
import os


def configure_logging(log_level: str) -> None:
    level_name = (log_level or "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(level=level)

    # SQLAlchemy engine logs are very noisy at INFO; suppress unless debugging.
    sqlalchemy_level_name = os.getenv("SQLALCHEMY_LOG_LEVEL", "").upper()
    if sqlalchemy_level_name:
        engine_level = getattr(logging, sqlalchemy_level_name, logging.WARNING)
    else:
        engine_level = logging.INFO if level <= logging.DEBUG else logging.WARNING
    logging.getLogger("sqlalchemy.engine").setLevel(engine_level)
    logging.getLogger("sqlalchemy.engine.Engine").setLevel(engine_level)
