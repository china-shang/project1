#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import sys

logging_level = logging.DEBUG

def get_logger(module_name = __name__):
    logger = logging.getLogger(module_name)
    logger.setLevel(logging_level)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s  - %(threadName)s - %(name)s - %(message)s', '%m/%d %H:%M:%S')
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    ch.setLevel(logging_level)
    ch.addFilter(lambda record:record.levelno == logging.INFO )

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - - %(threadName)s -%(name)s - %(funcName)s -  %(message)s', '%m/%d %H:%M:%S')
    ch1 = logging.StreamHandler()
    ch1.setFormatter(formatter)
    ch1.setLevel(logging_level)
    ch1.addFilter(lambda record:record.levelno != logging.INFO )

    logger.addHandler(ch)
    logger.addHandler(ch1)

    return logger

if __name__ == "__main__":
    logger = get_logger()
    logger.info("this is test info")
    logger.warn("this is test warn")
    logger.error("this is test error")
