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
from gitee_fetch_users import TaskQueue, init_queue, Worker


logger = get_logger(__name__)
logger.setLevel(logging.INFO)

class ProjectTaskQueue(TaskQueue):
    def __init__(self,maxsize = 100000):
        super().__init__(maxsize)

    def get(self):
        with self._get_cv:
            if not self.empty():
                logger.info(f"remaining: {self.qsize()}")
            else:
                logger.warning(f"no task")
                raise KeyboardInterrupt

                #self.change_task()

                self._get_cv.wait_for(lambda:not self.empty())
            item = super(TaskQueue, self).get()
            #self._set.remove(item)
            self._put_cv.notify(self.maxsize - self.qsize())
        return item


class ProjectWorker(Worker):
    def __init__(self, queue:TaskQueue, only_user = False):
        self._infos = []
        self._projects = []
        super().__init__(queue, False)

    def _do(self):
        if self._now_url is None:
            self.stop()
            return
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
        self._fetch_projects(sp)
        #self._fetch_users()

    def _extract_info(self, sp:Soup):
        r = [self._now_url]
        r += super()._extract_info(sp)
        self._infos.append(r)
        if len(self._infos) > 1000:
            self._save_infos()

    def _extract_project(self, sp:Soup)->list:
        res = super()._extract_project(sp)

        self._projects += res

        if len(self._projects) > 1000:
            self._save_projects()
        else:
            logger.info(f"has {len(self._projects)} project")

    def _save_infos(self):
        if len(self._infos) == 0:
            return
        logger.info("_save_infos ing ")
        file_name = "infos" + str(int(time.time() * 1000))
        with open(file_name, "w") as fp:
            json.dump(self._infos, fp)

        self._infos.clear()

    def _save_projects(self):
        if len(self._projects) == 0:
            return
        global lock, all_project
        logger.info("_save_projects ing ")
        file_name = "projects" + str(int(time.time() * 1000))
        with lock:
            all_project += len(self._projects)
            logger.info(f"All get {all_project} projects")
        with open(file_name, "w") as fp:
            json.dump(self._projects, fp)

        self._projects.clear()

    def stop(self):
        self._running = False
        self._save_infos()
        self._save_projects()
            
def init_queue(q):
    l = []
    with open("users", "r") as fp:
        l = [i.strip("\n") for i in fp.readlines() ]
    for i in l:
        q.put(i)


def _test():
    q = ProjectTaskQueue()
    init_queue(q)
    worker = ProjectWorker(q)
    worker.do()

all_project = 0
lock = threading.Lock()
if __name__ == "__main__":
    futs = []
    workers = []
    max_workers = 20
    try:
        q = ProjectTaskQueue()
        init_queue(q)
        executor = ThreadPoolExecutor(max_workers = max_workers )
        for i in range(max_workers):
            worker = ProjectWorker(q)
            workers.append(worker)
            fut = executor.submit(worker.do)
            futs.append(fut)

        for fut in concurrent.futures.as_completed(futs):
            fut.result()
    except KeyboardInterrupt:

        logger.warning("start stop worker sleep")
        time.sleep(5)
        logger.warning("start stop worker, and save file")
        for i in workers:
            i.stop()
    finally:
        logger.warning("start save")
        logger.warning("start end, quitting")
        for fut in concurrent.futures.as_completed(futs):
            fut.result()
        else:
            logger.info("all stop")

