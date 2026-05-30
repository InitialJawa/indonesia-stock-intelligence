import logging
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(
    exist_ok=True
)

LOG_FILE = (
    LOG_DIR
    / "isi.log"
)


def get_logger(name):

    logger = logging.getLogger(
        name
    )

    logger.setLevel(
        logging.INFO
    )

    if not logger.handlers:

        formatter = logging.Formatter(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        )

        file_handler = (
            logging.FileHandler(
                LOG_FILE
            )
        )

        file_handler.setFormatter(
            formatter
        )

        logger.addHandler(
            file_handler
        )

    return logger