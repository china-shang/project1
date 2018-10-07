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
from gitee_1 import fetch_one_only, Model
import logging


logger = get_logger(__name__)
logger.setLevel(logging.INFO)

#TODO:fetch all users then change to fetch project
#



class TaskQueue(queue.Queue):
    def __init__(self, maxsize = 100000):
        self.maxsize = maxsize
        self._set = set()
        self._lock = threading.RLock()
        self._put_cv = threading.Condition(self._lock)
        self._get_cv = threading.Condition(self._lock)
        self.count = 0
        self.workers = []
        self._last = time.time()
        self._during = 60
        super().__init__(self.maxsize)

    def add_worker(self, worker):
        self.workers.append(worker)

    def add_workers(self, workers):
        self.workers += workers

    def change_task(self):
        for i in self.workers:
            i.to_get_project()

    def save(self):
        file_name = str(int(time.time()))
        s = ""
        with self._lock:
            for i in self._set:
                s += i + "\n"
        with open(file_name, "w") as fp:
            fp.writelines(s)

    def put(self, item, block = True, timeout = None):
        with self._put_cv:
            if item in self._set:
                logger.info(f"{item} has in queue , can not put in")
                return False
            if not self.full():
                pass
            else:
                self._put_cv.wait_for(lambda :not self.full())
            self.count += 1
            logger.info(f"{item} put in , now count = {self.count}")
            super().put(item)

            self._set.add(item)
            self._get_cv.notify(self.qsize())
            return True

    def get(self, block = True, timeout = None):
        with self._get_cv:
            if time.time() - self._last > self._during:
                self.save()

            if not self.empty():
                pass
            else:
                logger.warning(f"no task")
                self.save()
                #self.change_task()

                self._get_cv.wait_for(lambda:not self.empty())
            item = super().get()
            #self._set.remove(item)
            self._put_cv.notify(self.maxsize - self.qsize())
        return item
    

def init_queue(q):
    for i in range(ord('a'), ord('z') + 1):
        l = fetch_one_only(i, 1)
        for i in l:
            item = i.url.split("/")[1]
            logger.debug(item)
            q.put(item)

class Worker(object):
    def __init__(self, queue:TaskQueue, only_user = False):
        self._only_user = only_user
        self._url_prefix = "https://gitee.com/"
        self._q = queue
        self._running = True

    def to_get_project(self):
        self._only_user = False

    def do(self):
        while self._running:
            self._now_url = self._q.get()
            logger.info(f"_now_url = {self._now_url}")
            self._do()

    def stop(self):
        self._running = False
        logger.info(f"worker stopping")

    def _do(self):
        self._project_url_prefix = self._url_prefix + self._now_url + "/projects/" 
        resp = Get(self._project_url_prefix)
        sp=Soup(resp.text,"lxml")

        if not resp.ok:
            logger.warning(f"Request error, code = {resp.status_code}, reason = {resp.reason}")
            return
        error = sp.select_one(".error h3")
        if error:
            logger.warning(f"page error, error = {error.text}")
            return

        self._extract_info(sp)
        if not self._only_user:
            self._fetch_projects(sp)
        self._fetch_users()

    def _fetch_projects(self, sp:Soup):
        count = int(sp.select_one(".circular").text)
        self._extract_project(sp)
        t = sp.select(".pagination > a.item")
        logger.info(f"has {count} project page= {len(t)}")
        if len(t) < 2:
            pages = 1
        else:
            pages = int(t[-2].text)

        for i in range(1, pages + 1):
            if not self._running:
                break
            self._fetch_project_page(i)

    def _extract_info(self, sp:Soup):
        items = sp.select(".follow-num")
        try:
            followers = int(items[0].text)
            stars = int(items[1].text)
            following = int(items[2].text)
            watches = int(items[3].text)
        except Exception as e:
            print(items)
        logger.info( f"followers = {followers}, stars = {stars}, following = {following}, watches = {watches}")

    def _extract_users(self, sp:Soup):
        users = []
        for i in sp.select(".user-list-item > a"):
            users.append(i['href'])
        for i in users:
            self._q.put(i.split("/")[1])
        logger.info(f"get users{users}")
    
    def _fetch_users(self):
        self._followers_prefix_url = f"{self._url_prefix}{self._now_url}/followers/" 
        resp = Get(self._followers_prefix_url)
        sp = Soup(resp.text, "lxml")
        self._extract_users(sp)
        t = sp.select(".pagination > a.item")
        if len(t) < 2:
            pages = 1
        else:
            pages = int(t[-2].text)
        for i in range(1, pages + 1):
            if not self._running:
                break
            self._fetch_user_page(i)

        self._following_prefix_url = f"{self._url_prefix}{self._now_url}/following/" 
        resp = Get(self._following_prefix_url)
        sp = Soup(resp.text, "lxml")
        self._extract_users(sp)
        t = sp.select(".pagination > a.item")
        if len(t) < 2:
            pages = 1
        else:
            pages = int(t[-2].text)
        for i in range(1, pages + 1):
            self._fetch_user_page(i, False)
            if not self._running:
                break

    def _fetch_user_page(self, page:int, follower = True):
        if follower:
            logger.info(f"now fetch follower, page = {page}")
            resp = Get(self._followers_prefix_url +f"?page={page}" )
        else:
            logger.info(f"now fetch following, page = {page}")
            resp = Get(self._following_prefix_url +f"?page={page}" )

        sp = Soup(resp.text, "lxml")
        self._extract_users(sp)

    def _fetch_project_page(self, page):
        header = {
            'Accept': '*/*;q=0.5, text/javascript, application/javascript, application/ecmascript, application/x-ecmascript',
            'X-Requested-With': 'XMLHttpRequest'}
        logger.info(f"now fetch project, page = {page}")
        resp = Get(f"{self._project_url_prefix}{page}", headers = header)
        s = self._xml_response(resp.text)
        self._extract_project(Soup(s, "lxml"))

    def _xml_response(self, text:str)->str:
        s = text.split("$")[1]
        s = s.split("html(")[0]
        s = s.rsplit(")")[0]
        s = s.replace("\\n","\n")
        s = s.replace("\\n","\n")
        s = s.replace("\\'","'")
        s = s.replace('\\"','"')
        s = s.replace('\\/','/')
        return s

    def _extract_project(self, sp:Soup)->list:
        projects = sp.select("div.project")
        ms = []
        for project in projects:
            if not self._running:
                break
            desc = project.select_one(".description").text
            time = project.select(".create-time > span")[0].text
            url =  project.select(".repository")[0]['href']
            name =  project.select(".repository")[0].text
            lang = project.select(".label")
            if len(lang) == 0:
                #logger.warning(f"lang is None, project = {project}")
                label = ""
            else:
                label = lang[0].text
            watch = int(project.select("li.watch > a")[1].text)#index :1 3 5
            star = int(project.select("li.star > a")[1].text)#index :1 3 5
            fork = int(project.select("li.fork > a")[1].text)#index :1 3 5
            m = Model(desc, time, watch, star, fork, name, url, label)
            ms.append(m)
            logger.info(f"fork = {fork},star = {star},watch = {watch},label = {label},url = {url},time = {time},desc = {desc}")

import random
def put(q):
    while True:
        i = random.randint(0, 1000)
        q.put(i)
        logger.debug("put % d" % i)
        time.sleep(1)
def get(q):
    while True:
        i = q.get()
        logger.debug("get  % d" % i)
        time.sleep(1)

def test():
    try:
        workers = ThreadPoolExecutor(100, "test")
        q = TaskQueue()
        fs = []
        for i in range(100):
            fs.append(workers.submit(put, q))
            fs.append(workers.submit(get, q))

        for i in concurrent.futures.as_completed(fs):
            i.result()
    except Exception as e:
        exit()

def test():
    q = TaskQueue()
    init_queue(q)
    while True:
        url = q.get()
        resp = Get(f"https://gitee.com/{url}/projects")
        sp = Soup(resp.text, "lxml")
        print(resp.text)
        print(f"url = {url}")

if __name__ == "__main__":
    futs = []
    workers = []
    max_workers = 100
    try:
        q = TaskQueue()
        init_queue(q)
        executor = ThreadPoolExecutor(max_workers = max_workers )
        for i in range(max_workers):
            worker = Worker(q, only_user = True)
            workers.append(worker)
            fut = executor.submit(worker.do)
            futs.append(fut)

        for fut in concurrent.futures.as_completed(futs):
            fut.result()
    except (KeyboardInterrupt, SystemExit):
        logger.warning("start stop worker, and save file")
        for i in workers:
            i.stop()
    finally:
        logger.warning("start save")
        q.save()
        logger.warning("start end, quitting")
        for fut in concurrent.futures.as_completed(futs):
            fut.result()
        else:
            logger.info("all stop")

