#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import requests 
from requests import Session, Request, get as Get
from bs4 import BeautifulSoup as Soup

import concurrent.futures  
import threading
from concurrent.futures  import ThreadPoolExecutor

i = "a"
page = "1"

def f(i, page):
    resp = Get(f"https://gitee.com/search?page={page}&q={i}&sort=watches_count&type=")
    #print(resp.text)
    sp = Soup(resp.text, "lxml")

    items = sp.select(".content-list > div")
    item = items[0]
    name = item.select_one(".ellipsis")['title']
    label = item.select_one(".label")
    if(label is None):
        label = ""
    else:
        label = label.text
    desc = item.select_one(".description").text[1:]
    time = item.select_one(".time").text
    watch = item.select(".metas .item span")[0].text
    star = item.select(".metas .item span")[1].text
    fork = item.select(".metas .item span")[2].text

    print(f"name = {name} type = {label} \ndesc = {desc}update-time = {time}\nwatch_num = {watch} star_num = {star} fork_num = {fork}")


executor = ThreadPoolExecutor(max_workers = 100)
for i in range(ord('a'), ord('z') + 1):
    i = chr(i)
    futures_to_page = {executor.submit(f,i,page) :page for page in range(20)}

for f in concurrent.futures.as_completed(futures_to_page):
    executor.shutdown()
    print(f.result())

