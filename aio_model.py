#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import time
import logging
from logger import get_logger
import logging
from model import Chain, Type
import asyncio


logger = get_logger(__name__)
logger.setLevel(logging.DEBUG)
class Owner(dict):
    User = 1
    Org = 2
    Unkonwn = 0
    def __init__(self, login, type = 0):
        self.login = login
        self.type = type
        self['login'] = login
        self['type'] = type

    def __hash__(self):
        return hash(self.login)

    def __eq__(self, other):
        return self.login == other.login 


class Result(object):
    def __init__(self, owners,repos):
        self.owners = []
        self.repos = []

class OwnerQueue(asyncio.Queue):
    def __init__(self, max_size = 0,  *args , loop = None):
        super().__init__(max_size,  *args, loop = loop)
        self._set = set()

    async def put(self, owner:Owner, anyway = False):
        if owner.login in self._set :
            logger.debug(f"{owner.login} has in queue")
            return False
        self._set.add(owner.login)
        await super().put(owner)
        return True

    async def get(self):
        logger.info(f"remining {self.qsize()}")
        result = await super().get()
        return result

    def has(self, item):
        result = item in self._set
        #print(f"{item} in is {result}")
        return result



async def test():
    pass


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test())


