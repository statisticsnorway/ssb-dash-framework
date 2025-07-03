import logging
import sys


def enable_app_logging(level="info"):
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
        level = logging.DEBUG
    elif level == "info":
        level = logging.INFO
    elif level == "warning":
        level = logging.WARNING
    elif level == "error":
        level = logging.ERROR
    elif level == "critical":
        level = logging.CRITICAL
    else:
        raise ValueError(f"Invalid logging level: {level}")
    logger = logging.getLogger("ssb_dash_framework")
    logger.setLevel(level)

    console_handler = logging.StreamHandler(sys.stdout)
    file_handler = logging.FileHandler("app.log", mode="a")

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    for handler in [console_handler, file_handler]:
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.propagate = (
        False  # Nødvendig pga jupyter som insisterer på å legge til enda en handler.
    )

    logger.info("App started.")
