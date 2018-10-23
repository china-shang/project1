#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import aiomysql
import json
from baseuser import  * 
from logger import get_logger
import logging

logger = get_logger(__name__)
logger.setLevel(logging.INFO)

body = """
CREATE TABLE IF NOT EXISTS `git_owner`(
   `name` VARCHAR(100) NOT NULL,
   `is_org`  BOOL DEFAULT FALSE,
   `create_tm` TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
   `fetched` BOOL DEFAULT FALSE, 
   `users_fetched` BOOL DEFAULT FALSE, 
   PRIMARY KEY ( `name` ), 
   INDEX `name_idx` (`name`)
)DEFAULT CHARSET=utf8;

"""

with open("mysql.json") as fp:
    _config = json.load(fp)

class LackUser(Exception):
    pass

class QueuePool(object):
    NO = 0
    HAS_GET_USERS = 1
    HAS_FETCH = 2
    def __init__(self):
        self._fetched = set()
        self._user_fetched = set()
        self._will_user_fetched = set()
        self._will_fetched = set()
        self._start_update_count = 10
        self._running = True
        self._putting = False
        self._will_put = set()
        self._getting = False

    async def create_pool(self):
        self.pool = await aiomysql.create_pool(**_config, autocommit=True, connect_timeout = 40)

    async def stop(self):
        self._running = False
        await self.pool.close()

    async def get_users(self, produce = False):
        # if getting , then wait to complete
        while self._getting:
            logger.info("get , but now getting, ")
            await asyncio.sleep(0.3)

        self._getting = True
        t = await self._fetch(produce)
        self._getting = False

        logger.info(f"{self._will_fetched}, {self._will_user_fetched}")
        logger.info(f"get_users {t}")
        return t


    def put_user(self, user):
        self._will_put.add(user)
        if len(self._will_put) > 10:
            logger.debug(f" will put to mysqlk")
            if not self._putting:
                asyncio.ensure_future(self.put_users(self._will_put.copy()))
                self._putting = True
                self._will_put.clear()
            else:
                logger.debug("but now putting, so wait")

    async def put_users(self, users:set):
        existed = await self._check_exist(users)
        if existed:
            users.difference_update(existed)
        logger.info(f"will put users = {users}")
        await self._insert(users)
        self._putting = False

    def complete(self,data,  produce = False):
        if isinstance(data, str):
            user = data
        elif isinstance(data, BaseUser):
            user = data.name
        else:
            logger.error(f"{type(data)}")
            raise TypeError

        #logger.debug("add complete")
        if produce:
            self._user_fetched.add(user)
        else:
            self._fetched.add(user)

    async def update(self):
        async def do():
            while self._running:
                l1, l2 = len(self._fetched), len(self._user_fetched)
                #logger.debug(f" updatingl1 = {l1}, l2 = {l2}")
                if l1 + l2 < self._start_update_count:
                    await asyncio.sleep(3)
                    continue

                #logger.debug("will updating")
                s1, s2 = self._fetched.copy(), self._user_fetched.copy()
                await self._update(s1, s2)

                self._fetched.difference_update(s1)
                self._user_fetched.difference_update(s2)
                self._will_fetched.difference_update(s1)
                self._will_user_fetched.difference_update(s1)
                del s1, s2

        await do()

    async def _update(self,fetched, all_fetched):
        def gen_body_fetched():
            names = ""
            for i in map(lambda x:f"'{x}',", fetched):
                names = f"{names}{i}"
            names = f"{names[:-1]}"
            body = f"UPDATE git_owner SET fetched = True where name in ({names})"
            logger.debug(body)
            return body
        def gen_body_users_fetched():
            names = ""
            for i in map(lambda x:f"'{x}',", all_fetched):
                names = f"{names}{i}"
            names = f"{names[:-1]}"

            body = f"UPDATE git_owner SET users_fetched = True where name in ({names})"
            logger.debug(body)
            return body

        logger.debug("update")
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                if len(fetched) > 0:
                    await cur.execute(gen_body_fetched())
                if len(all_fetched) > 0:
                    await cur.execute(gen_body_users_fetched())

    async def _insert(self, users):
        def gen_body():
            values = ""
            for u in users:
                values = f"{values}('{u.name}', {u.is_org}),"
            values = values[:-1]
            body = f"INSERT INTO git_owner (name,is_org) VALUES {values};"
            return body
        if (not users) or len(users) == 0:
            return
        if len(users) == 0:
            return
        body = gen_body()
        logger.debug(body)
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                #await cur.executemany("INSERT INTO git_owner (name, is_org) VALUES (%s, %s)",[(i.name, i.is_org) for i in users] )
                await cur.execute(body)
                result = await cur.fetchall()
                logger.debug(f"resutl = {result}, count = {cur.rowcount}")

    async def _check_exist(self, users):
        def gen_body():
            names = ""
            for name in map(lambda x:f'"{x.name}"', users):
                names = f"{names}{name},"
            names = f"{names[:-1]}"

            body = f'SELECT name FROM git_owner where name in ({names});'
            return body

        body = gen_body()
        logger.debug(body)
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(body)
                t = await cur.fetchall()
                result = set([i[0] for i in t])

                logger.debug(f"result  = {result}")
                return result

    async def _fetch(self, produce = False):
        if produce:
            result  = await self._fetch_produce()
            return result 

        def gen_body():
            names = ""
            s = self._fetched | self._will_fetched
            for i in map(lambda x:f"'{x}',", s):
                names = f"{names}{i}"
            names = f"{names[:-1]}"

            if not s or len(s) == 0:
                body = f"SELECT  name,is_org FROM git_owner where fetched=FALSE  LIMIT 10;"
            else:
                body = f"SELECT  name, is_org FROM git_owner where fetched=FALSE AND name NOT IN ({names}) LIMIT 10;"
            logger.info(body)
            return body

        body = gen_body()
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(body)
                t = await cur.fetchall()
                self._will_fetched.update(set([i[0] for i in t]))
                result = set([BaseUser(i[0], i[1]) for i in t])
                #logger.debug(result)
                await cur.execute("SELECT count(*) FROM git_owner where fetched=False GROUP BY name")
                remain = cur.rowcount
                if remain < 100:
                    pass
                    #TODO raise Lack user
                return result

    async def _fetch_produce(self):
        def gen_body():
            names = ""
            s = self._user_fetched | self._will_user_fetched
            for i in map(lambda x:f"'{x}',", s):
                names = f"{names}{i}"
            names = f"{names[:-1]}"

            if not s or len(s) == 0:
                body = f"SELECT  name, is_org FROM git_owner where users_fetched=FALSE  LIMIT 10;"
            else:
                body = f"SELECT  name, is_org FROM git_owner where users_fetched=FALSE AND name NOT IN ({names}) LIMIT 10;"
            logger.debug(body)
            return body

        body = gen_body()
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(body)
                t = await cur.fetchall()
                self._will_user_fetched.update(set([i[0] for i in t]))
                result = set([BaseUser(i[0], i[1]) for i in t])
                return result

async def create_table(loop):
    conn = await aiomysql.connect(**_config,loop = loop)
    async with conn.cursor() as cur:
        await cur.execute('DROP TABLE IF EXISTS git_owner;')
        await cur.execute(body)
        #await cur.execute('INSERT INTO git_owner (name, is_org ) VALUES("上的反思的", TrUE);')
        await cur.execute('select *, count( * ) from git_owner where name in ("上的反思的", "4") group by name;')

        res = await cur.fetchall()

        logger.debug(res)
        logger.debug("has recreate database")
    conn.close()

def test():
    pass

#test()
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(create_table(loop))
