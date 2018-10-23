#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import time
import logging
from logger import get_logger
import logging
from model import Chain, Type
from baseuser import BaseUser
import asyncio
from aio_mysql import QueuePool, LackUser


logger = get_logger(__name__)
logger.setLevel(logging.DEBUG)

class Result(object):
    def __init__(self, owners,repos):
        self.owners = []
        self.repos = []

class OwnerQueue(asyncio.Queue):
    def __init__(self, max_size = 0,  *args , loop = None):
        super().__init__(max_size,  *args, loop = loop)
        self._users = set()
        self._produce_users = set()
        self.pool = QueuePool()
        asyncio.ensure_future(self.pool.update())

    async def put(self, owner:BaseUser):
        self.pool.put_user(owner)
        return True

    async def get(self):
        #logger.info(f"remining {self.qsize()}")
        if len(self._users) == 0:
            self._users = await self.pool.get_users()
            if not self._users or len(self._users) < 4:
                logger.warning("lack user")
                raise LackUser
        result = self._users.pop()
        return result

    async def get_for_produce(self):

        self._produce_users = await self.pool.get_users(produce = True)
        while not self._produce_users or len(self._produce_users) == 0:
            logger.warning(f"can not fetch user")
            await asyncio.sleep(3)
            self._produce_users = await self.pool.get_users(produce = True)
        result = self._produce_users.pop()
        return result

    def complete(self, owner, produce = False):
        logger.info(f"complete {owner}")
        self.pool.complete(owner, produce)


async def test():
    test_users = []
    for i in range(20, 31):
        test_users.append(BaseUser(str(i), i % 2))
    q = OwnerQueue()
    await q.pool.create_pool()

    for i in test_users:
        await q.put(i)
    for i in test_users:
        try:
            u = await q.get()
            q.complete(u)
            logger.debug(f"get user:{u} in no produce")
        except LackUser:
            u = await q.get_for_produce()
            logger.debug(f"get user:{u} in lock user")

    await asyncio.sleep(100)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test())


