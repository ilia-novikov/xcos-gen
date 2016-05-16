import logging

__version__ = '0.2'
__author__ = 'Ilia Novikov <ilia.novikov@live.ru>'


def get_logger(name):
    formatter = logging.Formatter(
        fmt='xcos-gen::{0} %(levelname)s @ [%(asctime)s] %(message)s'.format(name),
        datefmt='%d-%m-%Y / %H:%M:%S'
    )
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    return logger
