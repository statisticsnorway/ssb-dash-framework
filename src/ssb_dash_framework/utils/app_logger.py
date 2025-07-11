import logging
import sys

_LOGGING_ENABLED: bool = False


def enable_app_logging(level: str = "info", log_to_file: bool = False) -> None:
    """This function enables logging for the editing framework.

    Args:
        level (str): The logging level to set. Can be one of "debug", "info", "warning", "error", or "critical".
            Defaults to "info".
        log_to_file (bool): if True, logs will also be written to a file named "app.log". Defaults to False.
            This file should not be saved in the repository, as it will contain sensitive information in the logs.

    Raises:
        ValueError: If the provided logging level is not valid.
        RuntimeError: If logging is already enabled.

    Note:
        The logging output will be sent to both the console and a file named "app.log".
        Also adds a logging message to indicate that the app was started. This is to make it possible to differentaiate different sessions.
    """
    if globals()["_LOGGING_ENABLED"]:
        raise RuntimeError(
            "ssb-dash-framework logger is already enabled, either set 'enable_logging' to False in app_setup or make sure you are not running 'enable_app_logging()' directly."
        )
    level = level.lower()
    if level == "debug":
        chosen_level = logging.DEBUG
    elif level == "info":
        chosen_level = logging.INFO
    elif level == "warning":
        chosen_level = logging.WARNING
    elif level == "error":
        chosen_level = logging.ERROR
    elif level == "critical":
        chosen_level = logging.CRITICAL
    else:
        raise ValueError(f"Invalid logging level: {level}")
    logger = logging.getLogger("ssb_dash_framework")
    logger.setLevel(chosen_level)
    handlers: list[logging.Handler] = []
    console_handler = logging.StreamHandler(sys.stdout)
    handlers.append(console_handler)
    if log_to_file:
        file_handler = logging.FileHandler("app.log", mode="a")
        handlers.append(file_handler)

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s",
    )
    for handler in handlers:
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.propagate = (
        False  # Nødvendig pga jupyter som insisterer på å legge til enda en handler.
    )
    globals()["_LOGGING_ENABLED"] = True

    logger.info("App logging started.")
