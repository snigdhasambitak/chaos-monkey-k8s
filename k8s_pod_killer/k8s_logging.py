import logging
from os import getenv

def _logging():
    logging.basicConfig(level=logging.INFO, format="-> [%(levelname)s] [%(asctime)s] %(message)s", datefmt="%Y-%m-%d %H:%M")
    if getenv("DEBUG") == "True":
        logging.getLogger(__name__).setLevel(logging.DEBUG)
    return logging.getLogger(__name__)
