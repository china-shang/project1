#!/usr/bin/env python1
# -*- coding: utf-8 -*-


import asyncio
import aiohttp
from aiohttp import ClientSession as Session
import json
from baseuser import  * 
from logger import get_logger
import logging
import functools

logger = get_logger(__name__)
logger.setLevel(logging.DEBUG)
server_addr = "0.0.0.0"
server_port = 1111

with open("mysql.json") as fp:
    _config = json.load(fp)

class LackUser(Exception):
    pass

class DBClient(object):
    def __init__(self, server, port):
        self.server = server
        self.port = port
        self._client = Session(timeout = aiohttp.ClientTimeout(total = 60), json_serialize = user_dumps)
        self._put_buffer = []
        self._complete_buffer = []
        self._get_buffer = set()
        self._get_buffer1 = set()
        self._putting = False
        self._completting = False
        self._getting = False
        self._getting1 = False

    def _has_error(self, resp):
        if resp.status != 200:
            logger.error(f"resp.status = {resp.status}, reason = {resp.reason}")
            return True
        return False

    async def get(self, produce = False):
        if produce:
            return await self.get_produce()

        if len(self._get_buffer) == 0:
            if not self._getting:
                self._getting = True
                res = await self._get()
                self._get_buffer = set([BaseUser(i['name'], i['is_org']) for i in res['data']])
            else:
                #has getting , now waitting get complete
                while self._getting:
                    await asyncio.sleep(1)

        if len(self._get_buffer) == 0:
            raise LackUser
        t = self._get_buffer.pop()
        return t

    async def get_produce(self):
        if len(self._get_buffer1) == 0:
            if not self._getting1:
                self._getting1 = True
                res = await self._get(True)
                self._get_buffer1 = set([BaseUser(i['name'], i['is_org']) for i in res['data']])
                if len(self._get_buffer1) == 0:
                    logger.error("total no task")
            else:
                #has getting , now waitting get complete
                while self._getting1:
                    await asyncio.sleep(1)

        t = self._get_buffer1.pop()
        return t

    def put(self, task):
        self._put_buffer.append(task)
        
        if not self._putting and len(self._put_buffer) > 1:
            self._putting = True
            asyncio.ensure_future(self._put())

    def complete(self, task, produce = False):
        if isinstance(task, BaseUser):
            task = task.name
        elif isinstance(task, str):
            pass
        elif isinstance(task, list):
            for i in task:
                self.complete(i)
        else:
            logger.error(f"type(task) is {type(task)}")

        self._complete_buffer.append((task, produce))

        if not self._completting and len(self._complete_buffer) > 1:
            asyncio.ensure_future(self._complete())
            self._completting = True

    async def _put(self):
        async with self._client.post(f"http://{self.server}:{self.port}/put", json = self._put_buffer ) as resp:
            if self._has_error(resp):
                pass

            res = await resp.json()
            logger.info(f"put {res}")
            self._put_buffer.clear()
            self._putting = False

    async def _complete(self):
        async with self._client.post(f"http://{self.server}:{self.port}/complete", json = self._complete_buffer ) as resp:
            if self._has_error(resp):
                pass

            res = await resp.json()
            logger.debug(res)
            self._put_buffer.clear()
            self._completting = False

    async def _get(self, produce = False):
        async with self._client.get(f"http://{self.server}:{self.port}/get", json = {"produce":produce}) as resp:
            if self._has_error(resp):
                pass

            res = await resp.json()
            logger.debug(res)
            if produce:
                self._getting1 = False
            else:
                self._getting = False

            return res


async def test():
    cl = DBClient(server_addr, server_port)
    for i in range(10):
        u = BaseUser(str(i))
        cl.put(i)

    await asyncio.sleep(100)

async def test():
    test_users = []
    for i in range(0, 11):
        test_users.append(BaseUser(str(i), i % 2))
    q = DBClient(server_addr, server_port)

    #for i in test_users:
        #q.put(i)
    for i in test_users:
        try:
            u = await q.get(True)
            u = await q.get()
            q.complete(u)
            logger.debug(f"get user:{u} ")

            logger.debug(f"get user:{u} in no produce")
        except LackUser:
            u = await q.get(True)
            logger.debug(f"get user:{u} in lock user")

    await asyncio.sleep(100)

#test()
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test())
