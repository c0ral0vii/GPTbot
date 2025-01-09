import logging
from logging.handlers import RotatingFileHandler
from src.config.config import settings


def setup_logger(name) -> logging.Logger:
    """
    Инициализация логгера

    :return:
    """

    logger = logging.getLogger(name)

    logger.setLevel(logging.DEBUG)

    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    if settings.get_debug_settings:
        debug_handler = logging.StreamHandler()
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(logging.Formatter(format))

        logger.addHandler(debug_handler)

    info_handler = RotatingFileHandler(
        f"logs/info.log", maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(logging.Formatter(format))

    error_handler = RotatingFileHandler(
        f"logs/error.log", maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(format))

    logger.addHandler(info_handler)
    logger.addHandler(error_handler)

    return logger
