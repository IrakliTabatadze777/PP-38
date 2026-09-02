import logging
from logging import StreamHandler
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logging():
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    root_logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '[%(levelname)s | %(asctime)s | %(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    console_handler = StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)


    file_handler = RotatingFileHandler(
        log_dir / 'app.log',
        maxBytes=1000000,
        backupCount=10,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)


    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)



