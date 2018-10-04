#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import requests 
from requests import Session, Request, get as Get
from bs4 import BeautifulSoup as Soup

import json
import queue
import concurrent.futures  
import threading
from concurrent.futures  import ThreadPoolExecutor
from logger import get_logger

logger = get_logger(__name__)

s = "0123456789 的一了是我不在人们有来他这上着个地到大里说就去子得也和那要下看天时过出小么起你都把好还多没为又可家学只以主会样年想能生同老中十从自面前头道它后然走很像见两用她国动进成回什边作对开而己些现山民候经发工向  事命给长水几义三声于高正妈手知理眼志点心战二问但身方实吃做叫当住听革打呢真党全才四已所敌之最光产情路分总条白话东席次亲如被花口放儿常西气五第使写军吧文运再果怎定许快明行因别飞外树物活部门无往船望新带队  先力完间却站代员机更九您每风级跟笑啊孩万少直意夜比阶连车重便斗马哪化太指变社似士者干石满日决百原拿群究各六本思解立河爸村八难早论吗根共让相研今其书坐接应关信觉死步反处记将千找争领或师结块跑谁草越字加脚  紧爱等习阵怕月青半火法题建赶位唱海七女任件准张团屋爷离色脸片科倒睛利世病刚且由送切星导晚表够整认响雪流未场该并底深刻平伟忙提确近亮轻讲农古黑告界拉名呀土清阳照办史改历转画造嘴此治北必服雨穿父内识验传  业菜爬睡兴形量咱观苦体众通冲合破友度术饭公旁房极南枪读沙岁线野坚空收算至政城劳落钱特围弟胜教热展包歌类渐强数乡呼性音答哥际旧神座章帮啦受系令跳非何牛取入岸敢掉忽种装顶急林停息句娘区衣般报叶压母慢叔背细"
i = "a"
page = "1"

class Model(dict):
    def __init__(self, desc,time,watch,star,fork, name, url): 
        self['desc'] = desc 
        self['time'] = time 
        self['watch'] = watch
        self['star'] = star 
        self['fork'] = fork 
        self['name'] = name 
        self['source'] = "gitee"
        self['url'] = url

class Models(object):
    def __init__(self, max_size = 100):
        self.max_size = max_size
        self.l = []
        self.running = True

    def update(self):
        while self.running:
            self.l.append(q.get())
            if len(self.l) >= self.max_size:
                self.save()

    def save(self):
        print("save item")
        file_name = str(int(time.time()))
        with open(file_name, "w") as f:
            json.dump(self.l, f)
        self.l.clear()

    def add(item:Model):
        print("add item")
        q.put(item)

def seek(q):
    resp = Get(f"https://gitee.com/search?page=1&q={q}&sort=watches_count&type=")
    sp = Soup(resp.text, "lxml")
    t = sp.select("#git-discover-page > a")
    if(len(t) < 2):
        return
    pages = int(t[-2].text)
    print(f"{q} = {pages}")
    types = ["Ruby", "JavaScript", "CSS", "Java", "C", "Python", "PHP", "CoffeeScript", "Objective-C", "C#", "C++", "Perl", "AutoHotkey", "Shell", "Go", "VimL", "Matlab", "ASP", "Rust", "Scala", "Lua", "ActionScript", "Assembly", "Erlang", "Arduino", "Clojure", "Common Lisp", "Scheme", "FORTRAN" , "Verilog"]
    if pages == 100:
        for type in types:
            print(f"in {type}")
            resp = Get(f"https://gitee.com/search?page=1&q={q}&sort=watches_count&type=")
            sp = Soup(resp.text, "lxml")
            t = sp.select("#git-discover-page > a")
            if(len(t) < 2):
                continue
            pages1 = int(t[-2].text)
            for i in range(1,pages1 + 1 ):
                f(q, i)
    else:
        for i in range(1,pages + 1 ):
            f(q, i)

    #with open("has","a") as fp:
        #fp.write(f"\n{q}\n{pages}\n")

def f(i, page):
    resp = Get(f"https://gitee.com/search?page={page}&q={i}&sort=stars_count&type=")
    #print(resp.text)
    sp = Soup(resp.text, "lxml")

    items = sp.select(".content-list > div")
    item = items[0]
    name = item.select_one(".ellipsis")['title']
    url = item.select_one(".ellipsis")['href']
    label = item.select_one(".label")
    if(label is None):
        label = ""
    else:
        label = label.text
    try:
        desc = item.select_one(".description").text[1:]
    except Exception as e:
        print(item)
        desc = ""
    try:
        time = item.select_one(".time").text
    except Exception as e:
        print(item)
        time = ""
    try:
        watch = item.select(".metas .item span")[0].text
    except Exception as e:
        print(e)
        watch = ""
    try:
        star = item.select(".metas .item span")[1].text
    except Exception as e:
        print(e)
        star = ""
    try:
        fork = item.select(".metas .item span")[2].text
    except Exception as e:
        print(e)
        fork = ""

    m = Model(desc, time, watch, star, fork, name, url)
    #print(name)
    #threading.currentThread().getName()
    print(f"name = {name} url = {url} type = {label} \ndesc = {desc}update-time = {time}\nwatch_num = {watch} star_num = {star} fork_num = {fork}\n")
    if(q.full()):
        logger.warn("full")
    q.put(m)

q = queue.Queue(100)
ms = Models()
executor = ThreadPoolExecutor(max_workers = 20)
fut = executor.submit(ms.update)

futures_to_page = {executor.submit(seek,q) : q for q in s}

for i in concurrent.futures.as_completed(futures_to_page):
    i.result()

futures_to_page = {executor.submit(seek,chr(q)) : q for q in range(ord('a'), ord('z') + 1)}

for i in concurrent.futures.as_completed(futures_to_page):
    i.result()
#seek("sdjfisodfjasoidfjasodifjasf")

