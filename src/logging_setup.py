import os
import logging
from logging.handlers import RotatingFileHandler


def setup_logger(logname, filename):
    """
    Creates a logging rotating file handlers for writing and
    size-based log file rotation

    """

    if not os.path.exists('../logs'):
        os.mkdir('../logs')

    log_format = '<%(asctime)s> [%(levelname)s] <%(lineno)s> <%(funcName)s> %(message)s'
    file_logger = RotatingFileHandler(filename, mode='a', maxBytes=500 * 1024 * 1024, backupCount=10)

    formatter = logging.Formatter(log_format, datefmt='%m/%d/%Y %I:%M:%S %p')
    file_logger.setFormatter(formatter)

    logger = logging.getLogger(logname)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_logger)
    return logger


logger = setup_logger('app', '../logs/app.log')
