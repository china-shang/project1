#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import requests 
from requests import Session, Request, get as Get
from bs4 import BeautifulSoup as Soup

import concurrent.futures  
import threading
from concurrent.futures  import ThreadPoolExecutor


executor = ThreadPoolExecutor(max_workers = 10)
for i in range(ord('a'), ord('z') + 1):
    def f(i, page):
        resp = Get(f"https://gitee.com/search?page={page}&q={i}&sort=watches_count&type=")
        print(resp.text)
        sp = Soup(resp.text, "lxml")
        print(f"threadName = {threading.current_thread().getName()}\ntitle = {sp.title.text}")
        return resp.status_code
    i = chr(i)
    futures_to_page = {executor.submit(f,i,page) :page for page in range(20)}

for f in concurrent.futures.as_completed(futures_to_page):
    executor.shutdown()
    print(f.result())





