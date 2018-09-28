#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from requests import Session,Request, get as Get, post as Post
from requests.exceptions import  * 
import requests
import time
import queue
import logging
from logger import get_logger
import threading

q = queue.Queue()
logger = get_logger(__name__)
api_url = "https://api.github.com/search/repositories"

def producer(url,  **kwargs):
    logger.info("produce one item")
    q.put((url, kwargs))

def consumer():
    logger.info("start consume")
    while True:
        url, params = q.get()
        send_req(url, params = params)

def send_req(url, params = None):
    def need_retry(resp):
        if(resp.status_code != requests.codes.ok):
            code = resp.status_code
            logger.warn(f"Warning response status_code = {code}, reason = {resp.reason}")
            return True

        remaining_count = int(resp.headers['X-RateLimit-Remaining'])
        logger.debug(f"X-RateLimit-Remaining  == {remaining_count}")
        if remaining_count == 0:
            return True

        return False
    
    def sleep_if_need(resp):
        remaining_count = int(resp.headers['X-RateLimit-Remaining'])
        if remaining_count == 0:
            logger.info("X-RateLimit-Remaining  == 0, sleeping")
            dead_line = int(resp.headers['X-RateLimit-Reset'])
            logger.debug(f"dead_line = {dead_line}")
            now_time = time.time()
            if(now_time > dead_line):
                sleep_during = 3
            else:
                sleep_during = dead_line - now_time + 3
            logger.info(f"sleep {sleep_during}s")
            time.sleep(sleep_during)

    session = Session()
    for i in range(3):
        try:
            logger.info("requesting")
            resp = session.get(url, params = params, timeout = 10)
        except RequestException as req_e:
            logger.warn(f"request_exception : {req_e}")
            continue
        except Exception as e:
            logger.warn(f"exception : {e}")
            continue
        
        logger.info("request completed")
        if need_retry(resp):
            sleep_if_need(resp)
            continue
        break # has been get result, so break loop
    else:
        logger.error("retry count  > 3")
        producer(url, **params)
        return None

    #get next_url and produce item
    next_url = resp.links.get("next", None)
    if next_url:
        producer(next_url['url'])
    else:
        logger.info("no next page")
    return resp


producer(api_url,q = "a", per_page = 1000)
producer(api_url,q = "b", per_page = 1000)
producer(api_url,q = "c", per_page = 1000)
producer(api_url,q = "d", per_page = 1000)

threads = []
for i in range(4):
    t = threading.Thread(target = consumer, daemon=True)
    threads.append(t)
    t.start()

try:
    time.sleep(100000)
except KeyboardInterrupt:
    exit()

logger = get_logger()
api_url = "https://api.github.com/search/repositories"

def send_req(url, params = None):
    def need_retry(resp):
        if(resp.status_code != requests.codes.ok):
            code = resp.status_code
            logger.warn(f"Warning response status_code = {code}, reason = {resp.reason}")
            return True

        remaining_count = int(resp.headers['X-RateLimit-Remaining'])
        if remaining_count == 0:
            return True

        return False
    
    def sleep_if_need(resp):
        remaining_count = int(resp.headers['X-RateLimit-Remaining'])
        if remaining_count == 0:
            logger.info("X-RateLimit-Remaining  == 0, sleeping")
            dead_line = int(resp.headers['X-RateLimit-Reset'])
            logger.debug(f"dead_line = {dead_line}")
            now_time = time.time()
            if(now_time > dead_line):
                sleep_during = 3
            else:
                sleep_during = dead_line - now_time + 3
            logger.info(f"sleep {sleep_during}s")
            time.sleep(sleep_during)

    session = Session()
    for i in range(3):
        try:
            logger.info("requesting")
            resp = session.get(url, params = params, timeout = 10)
        except RequestException as req_e:
            logger.warn(f"request_exception : {req_e}")
            continue
        except Exception as e:
            logger.warn(f"exception : {e}")
            continue
        
        if need_retry(resp):
            sleep_if_need(resp)
            continue
        logger.debug(f"X-RateLimit-Remaining  == {remaining_count}")
        return resp
    else:
        logger.error("error count  > 3")
        return None
    return resp

def get_respo_list(**kwargs)->list:
    resp = send_req(api_url, kwargs)
    #return resp
    for i in range(30):
        next_url = resp.links.get("next", None)
        if next_url:
            resp = send_req(next_url['url'])
        else:
            logger.info("no next page")
            break

if __name__ == "__main__":
    result = get_respo_list(q = "a", per_page = 1000)

