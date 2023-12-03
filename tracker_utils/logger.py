import logging


def logger(name: str):
    lg = logging.getLogger(name)
    lg.setLevel(logging.INFO)
    # create file handler which logs even debug messages
    fh = logging.FileHandler("logs\\tracker.log")
    fh.setLevel(logging.DEBUG)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    # create formatter and add it to the handlers
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # add the handlers to the logger
    lg.addHandler(fh)
    lg.addHandler(ch)
    return lg
