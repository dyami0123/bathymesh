import logging
import os
from copy import deepcopy
from typing import cast


def configure_application_logging() -> tuple[str, dict[str, object]]:
    """Configure app logger levels and return uvicorn logging config."""
    log_level_name = os.getenv("BATHYMESH_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, log_level_name, logging.INFO)

    # Ensure app loggers are not filtered before uvicorn applies dictConfig.
    logging.getLogger("bathy").setLevel(level)
    logging.getLogger("bathy").propagate = False

    uvicorn_log_config = _build_uvicorn_log_config(log_level_name)

    if log_level_name not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        return "info", uvicorn_log_config

    return log_level_name.lower(), uvicorn_log_config


def _build_uvicorn_log_config(log_level_name: str) -> dict[str, object]:
    """Build uvicorn logging config with level, file, and line in each record."""
    import uvicorn

    config: dict[str, object] = deepcopy(uvicorn.config.LOGGING_CONFIG)

    formatters = cast(dict[str, dict[str, object]], config["formatters"])
    formatters["default"][
        "fmt"
    ] = "%(asctime)s | %(levelprefix)s | %(filename)s:%(lineno)d | %(message)s"
    formatters["default"]["datefmt"] = "%H:%M:%S"
    formatters["access"]["fmt"] = (
        "%(asctime)s | %(levelprefix)s | %(filename)s:%(lineno)d | "
        '%(client_addr)s - "%(request_line)s" %(status_code)s'
    )
    formatters["access"]["datefmt"] = "%H:%M:%S"

    loggers = cast(dict[str, dict[str, object]], config["loggers"])
    loggers["bathy"] = {
        "handlers": ["default"],
        "level": log_level_name,
        "propagate": False,
    }
    loggers["uvicorn"]["level"] = log_level_name
    loggers["uvicorn.error"]["level"] = log_level_name
    loggers["uvicorn.access"]["level"] = log_level_name

    config["root"] = {
        "handlers": ["default"],
        "level": log_level_name,
    }

    return config
