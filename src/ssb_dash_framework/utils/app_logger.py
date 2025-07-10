import logging
import sys


def enable_app_logging(level: str = "info") -> None:
    """This function enables logging for the editing framework.

    Args:
        level (str): The logging level to set. Can be one of "debug", "info", "warning", "error", or "critical".
            Defaults to "info".

    Raises:
        ValueError: If the provided logging level is not valid.

    Note:
        The logging output will be sent to both the console and a file named "app.log".
        Also adds a logging message to indicate that the app was started. This is to make it possible to differentaiate different sessions.
    """
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

    console_handler = logging.StreamHandler(sys.stdout)
    file_handler = logging.FileHandler("app.log", mode="a")

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s",
    )
    handlers: list[logging.Handler] = [console_handler, file_handler]
    for handler in handlers:
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.propagate = (
        False  # Nødvendig pga jupyter som insisterer på å legge til enda en handler.
    )

    logger.info("App started.")
