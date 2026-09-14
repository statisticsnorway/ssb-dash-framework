import json
import logging
import sys
from datetime import datetime
from pathlib import Path


_LOGGING_ENABLED: bool = False


class JsonlFormatter(logging.Formatter):
    """Formats logging records as JSON Lines."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "time": datetime.fromtimestamp(record.created)
            .astimezone()
            .isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "source_file": record.filename,
            "module_name": None,
            "module_number": None,
            "function": record.funcName,
            "message": record.getMessage(),
        }

        return json.dumps(log_entry, ensure_ascii=False)


def enable_app_logging(
    level: str = "info",
    log_to_file: bool = False,
) -> None:
    """Enable logging for the editing framework.

    Args:
        level:
            Logging level. One of "debug", "info", "warning",
            "error", or "critical".

        log_to_file:
            If True, logs will also be written to
            "/home/onyxia/work/app.jsonl".

    Raises:
        TypeError:
            If level is not a string or log_to_file is not a bool.

        FileNotFoundError:
            If the work directory does not exist.

        ValueError:
            If the provided logging level is not valid.

        RuntimeError:
            If logging is already enabled.
    """
    global _LOGGING_ENABLED

    if not isinstance(level, str):
        raise TypeError(
            f"level must be str, received: {type(level)}"
        )

    if not isinstance(log_to_file, bool):
        raise TypeError(
            f"log_to_file must be bool, received: {type(log_to_file)}"
        )

    if _LOGGING_ENABLED:
        raise RuntimeError(
            "ssb-dash-framework logger is already enabled, "
            "either set 'enable_logging' to False in app_setup "
            "or make sure you are not running "
            "'enable_app_logging()' directly."
        )

    level = level.lower()

    level_mapping = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }

    if level not in level_mapping:
        raise ValueError(f"Invalid logging level: {level}")

    logger = logging.getLogger("ssb_dash_framework")
    logger.setLevel(level_mapping[level])

    # Prevent log messages from propagating to the root logger.
    # This avoids duplicate messages in Jupyter.
    logger.propagate = False

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)

    console_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - "
        "%(funcName)s - %(message)s"
    )

    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # JSONL file handler
    if log_to_file:
        log_path = Path("/home/onyxia/work/app.jsonl")

        if not log_path.parent.exists():
            raise FileNotFoundError(
                f"Directory does not exist: {log_path.parent}"
            )

        file_handler = logging.FileHandler(
            log_path,
            mode="a",
            encoding="utf-8",
        )

        file_handler.setFormatter(JsonlFormatter())
        logger.addHandler(file_handler)

    _LOGGING_ENABLED = True

    logger.info("App logging started.")