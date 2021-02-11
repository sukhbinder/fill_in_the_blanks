import os
import logging


def create_logger(name, path=os.getcwd(), mode="a", console=False):
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if console:
        c_handler = logging.StreamHandler()
        c_handler.setLevel(logging.INFO)
        c_format = logging.Formatter("%(levelname)s %(message)s")
        c_handler.setFormatter(c_format)
        logger.addHandler(c_handler)

    fname = os.path.join(path, "{}.log".format(name))
    f_handler = logging.FileHandler(fname, mode=mode)
    f_handler.setLevel(logging.DEBUG) 
    f_format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    f_handler.setFormatter(f_format)
    logger.addHandler(f_handler)
    logger.propagate = False

    return logger


def get_logger(name: str):
    logger = logging.getLogger(name)
    return logger