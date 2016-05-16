import logging


def get_logger():
    formatter = logging.Formatter(
        fmt='xcos-gen :: %(levelname)s @ [%(asctime)s] %(message)s',
        datefmt='%d-%m-%Y / %H:%M:%S'
    )
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    return logger
