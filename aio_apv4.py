#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import time
import random
import queue
import logging
from logger import get_logger
import logging
from model import Chain, Type
from aio_writer import Writer
from aio_model import  * 
from aiohttp import ClientSession as Session
import threading
import aiohttp
import asyncio
import itertools


last_fail_time = 0
min_fail_during = 0
fail_addition = 0
count = 0
logger = get_logger(__name__)
logger.setLevel(logging.DEBUG)
header = {
    "Authorization":"bearer 6d551a019223e4345e064de043d1fe46b9cd0260", 
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"
}
get_rate_chain = Chain("rateLimit").get("cost limit remaining resetAt")

async def fetch_users(q):
    search_user_chain = Chain("search")\
            (type = Type("REPOSITORY"), query = f"{q} sort:forks", first = 10)\
            .nodes\
            .on("Repository")\
            .get(Chain("owner").get("login"))
    async with Session(headers = header) as client:
        async with client.post("https://api.github.com/graphql", json =search_user_chain.to_dict() ) as resp:
            result = await resp.json()
            names = [node['owner']['login'] for node in result['data']['search']['nodes'] ]
            logger.info(f"names = {names}")
            return names

async def get_rate_limit():
    async with Session(headers = header) as client:
        async with client.post("https://api.github.com/graphql", json = get_rate_chain.to_dict()) as resp:
            result = await resp.json()
            logger.info(f"result = {result}")

async def handle_user(user:Owner):
    chain = Chain("user")\
            (login = user.login)\
            .get(Chain("followers")\
                (first = 100)\
                 .get(Chain("pageInfo")\
                     .get("endCursor hasNextPage"))\
                .nodes\
                .get("login"))\
            .get(Chain("following")\
                (first = 100)\
                 .get(Chain("pageInfo")\
                     .get("endCursor hasNextPage"))\
                .nodes\
                .get("login"))\
            .get(Chain("organizations")\
                (first = 10)\
                 .get(Chain("pageInfo")\
                     .get("endCursor hasNextPage"))\
                .nodes\
                .get("login"))

    async with Session(headers = header) as client:
        async with client.post("https://api.github.com/graphql", json = chain.to_dict()) as resp:
            data = await resp.json()
            if data['data']['user'] is None:
                return None
            #print(data)
            owners = []
            followers = [Owner(node['login'], Owner.User) 
                         for node in  data['data']['user']['followers']['nodes']]
            print(f"followers = {followers}")

            return result

async def handle_org(org:Owner):
    chain = Chain("organization")\
            (login = org.login)\
            .get(Chain("members")\
                (first = 10)\
                 .get(Chain("pageInfo")\
                     .get("endCursor hasNextPage"))\
                .nodes\
                .get("login"))
    async with Session(headers = header) as client:
        async with client.post("https://api.github.com/graphql", json = chain.to_dict()) as resp:
            result = await resp.json()
            return result

async def hanle_unknown(owner:Owner):
    result = await handle_user(owner)
    print("in unknown")
    if result is None:
        print("to org")
        result = await handle_org(owner)
    return result

async def fetch_data_from_user(q:asyncio.Queue):
    owner = await q.get()
    if owner.type == Owner.User:
        result = await handle_user(owner)
    if owner.type == Owner.Org:
        result = await handle_org(owner)
    else:
        result = await hanle_unknown(owner)

    logger.info(f"{owner.login}:{result['data']}")

class Worker(object):
    header = {
        "Authorization":"bearer 6d551a019223e4345e064de043d1fe46b9cd0260", 
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"
    }
    api_url = "https://api.github.com/graphql"
    def __init__(self):
        self._client = Session(headers = Worker.header)
        self._running = True

    async def do(self):
        pass

    async def _close(self):
        await self._client.close()

    async def __aenter__(self):
        if self._client.closed:
            self._client = Session(headers = Worker.header)
        return self

    async def __aexit__(self, exe_type, exc_value, traceback):
        await self._close()

class RateLimitWorker(Worker):
    def __init__(self):
        super().__init__()
        self._chain = Chain("rateLimit").get("cost limit remaining resetAt")

    async def do(self):
        async with self._client.post(self.api_url,json = self._chain.to_dict()) as resp:
            print(f"api_url = {self.api_url}")
            result = await resp.json()
            print(result)
            return result['data']

class InitWorker(Worker):
    def __init__(self, q:asyncio.Queue):
        super().__init__()
        self._q = q
        self._writer = Writer()

    async def do(self):
        owners = await self._do("a")
        for i in owners:
            await self._q.put(Owner(i))

    async def _do(self,q = "q"):
        chain = Chain("search")\
                (type = Type("REPOSITORY"), query = f"{q} sort:forks", first = 10)\
                .nodes\
                .on("Repository")\
                .get(Chain("owner").get("login"))
        async with self._client.post(self.api_url, json =chain.to_dict() ) as resp:
            result = await resp.json()
            names = [node['owner']['login'] for node in result['data']['search']['nodes'] ]
            logger.info(f"names = {names}")
            return names

class FetchWorker(Worker):
    def __init__(self, q:asyncio.Queue, writer_owners:Writer = None
                 , writer_repos:Writer = None):
        super().__init__()
        self._q = q
        self._writer_repos = writer_repos
        self._writer_owners = writer_owners

    async def do(self):
        global count
        while self._running:
            await self.fetch_data_from_user()
            count += 1
            logger.info(f"compete get {count} user data")

    async def _do(self):
        pass

    def extrack_repos(self, repos:list):
        #logger.info(f"get repos:{repos}")
        self._writer_repos.add_data(repos)

    def extract_owners(self, owners, type = Owner.Unkonwn):
        owners = [Owner(i["login"], type) for i in owners if not self._q.has(i['login'])]
        self._writer_owners.add_data(owners)
        #logger.info(f"get owners:{owners}")
        for i in owners:
            loop.create_task(self._q.put(i))

        logger.info(f"remining {self._q.qsize()}")

    async def handle_user(self, user:Owner):
        def generate_chain():
            chain = Chain("user")\
                    (login = user.login)

            if has_more_followers:
                chain = chain\
                    .get(Chain("followers")\
                        (first = 100, after = followers_end_cursor )\
                         .get(Chain("pageInfo")\
                             .get("endCursor hasNextPage"))\
                        .nodes\
                        .get("login"))

            if has_more_following:
                chain = chain\
                    .get(Chain("following")\
                        (first = 100, after = following_end_cursor)\
                         .get(Chain("pageInfo")\
                             .get("endCursor hasNextPage"))\
                        .nodes\
                        .get("login"))

            if has_more_repos:
                chain = chain\
                    .get(Chain("repositories")\
                        (first = 10, after = repos_end_cursor)\
                         .get(Chain("pageInfo")\
                             .get("endCursor hasNextPage"))\
                        .nodes\
                         .get('name', 'url','description','updatedAt', 'projectsUrl', 'forkCount')\
                         .get(Chain("languages")
                              (first = 10)\
                              .nodes\
                              .get("name"))
                         .get(Chain("stargazers")\
                             (first = 1)\
                             .get("totalCount"))\
                         .get(Chain("watchers")\
                             (first = 1)\
                             .get("totalCount"))\
                        )

            if has_more_orgs:
                chain = chain\
                    .get(Chain("organizations")\
                        (first = 10, after = orgs_end_cursor)\
                         .get(Chain("pageInfo")\
                             .get("endCursor hasNextPage"))\
                        .nodes\
                        .get("login"))
            return chain

        chain = Chain("user")\
                (login = user.login)\
                .get(Chain("followers")\
                    (first = 100)\
                     .get(Chain("pageInfo")\
                         .get("endCursor hasNextPage"))\
                    .nodes\
                    .get("login"))\
                .get(Chain("following")\
                    (first = 100)\
                     .get(Chain("pageInfo")\
                         .get("endCursor hasNextPage"))\
                    .nodes\
                    .get("login"))\
                .get(Chain("organizations")\
                    (first = 10)\
                     .get(Chain("pageInfo")\
                         .get("endCursor hasNextPage"))\
                    .nodes\
                    .get("login"))\
                .get(Chain("repositories")\
                    (first = 10)\
                     .get(Chain("pageInfo")\
                         .get("endCursor hasNextPage"))\
                    .nodes\
                     .get('name', 'url','description','updatedAt', 'projectsUrl', 'forkCount')\
                     .get(Chain("languages")
                          (first = 10)\
                          .nodes\
                          .get("name")))

        has_more_followers = True
        has_more_following = True
        has_more_orgs = True
        has_more_repos = True
        while self._running :
            async with self._client.post(self.api_url, json = chain.to_dict()) as resp:
                try:
                    raw_data = await resp.json()
                    if raw_data['data'] is None:
                        logger.warn(f"data is None, result = {raw_data}")
                        return None
                    if raw_data['data']['user'] is None:
                        logger.warn(f"data is None, result = {raw_data}")
                        return None
                    data = raw_data['data']
                except KeyError:
                    logger.error(f"result = {raw_data}")
                    if "abuse" in raw_data['documentation_url'] :
                        global last_fail_time,fail_addition, min_fail_during
                        if  last_fail_time == 0:
                            last_fail_time = time.time()

                        now = time.time()
                        now_fail_during = now - last_fail_time
                        last_fail_time = now 
                        if now_fail_during < min_fail_during:
                            fail_addition += 5

                        during = random.randint(10, 20)
                        during += fail_addition
                        logger.warning(f"has abuse , sleep{during}, fail_addition = {fail_addition}, min_fail_during = {min_fail_during}, now_fail_during = {now_fail_during}")
                        time.sleep(during)
                        async with RateLimitWorker() as worker:
                            result = await worker.do()
                            logger.info(result)
                        return 

                if has_more_followers:
                    has_more_followers = data['user']['followers']['pageInfo']['hasNextPage']
                    followers_end_cursor = data['user']['followers']['pageInfo']['endCursor']
                    self.extract_owners(data['user']['followers']['nodes'], Owner.User)

                if has_more_following:
                    has_more_following = data['user']['following']['pageInfo']['hasNextPage']
                    following_end_cursor = data['user']['following']['pageInfo']['endCursor']
                    self.extract_owners(data['user']['following']['nodes'], Owner.User)

                if has_more_repos:
                    has_more_repos = data['user']['repositories']['pageInfo']['hasNextPage']
                    repos_end_cursor = data['user']['repositories']['pageInfo']['endCursor']
                    self.extrack_repos(data['user']['repositories']['nodes'])

                if has_more_orgs:
                    has_more_orgs = data['user']['organizations']['pageInfo']['hasNextPage']
                    orgs_end_cursor = data['user']['organizations']['pageInfo']['endCursor']
                    self.extract_owners(data['user']['organizations']['nodes'], Owner.Org)

            # no anymore data need to get
            if not (has_more_orgs or has_more_repos or has_more_followers or has_more_following):
                logger.debug("no more data")
                break

            chain = generate_chain()

        return True
        #chain = Chain("user")\
                #(login = user.login)\
                #.get(Chain("followers")\
                    #(first = 100)\
                     #.get(Chain("pageInfo")\
                         #.get("endCursor hasNextPage"))\
                    #.nodes\
                    #.get("login"))\
                #.get(Chain("following")\
                    #(first = 100)\
                     #.get(Chain("pageInfo")\
                         #.get("endCursor hasNextPage"))\
                    #.nodes\
                    #.get("login"))\
                #.get(Chain("organizations")\
                    #(first = 10)\
                     #.get(Chain("pageInfo")\
                         #.get("endCursor hasNextPage"))\
                    #.nodes\
                    #.get("login"))\
                #.get(Chain("repositories")\
                    #(first = 10)\
                     #.get(Chain("pageInfo")\
                         #.get("endCursor hasNextPage"))\
                    #.nodes\
                     #.get('name', 'url','description','updatedAt', 'projectsUrl', 'forkCount')\
                     #.get(Chain("languages")
                          #(first = 10)\
                          #.nodes\
                          #.get("name"))
                     #.get(Chain("stargazers")\
                         #(first = 1)\
                         #.get("totalCount"))\
                     #.get(Chain("watchers")\
                         #(first = 1)\
                         #.get("totalCount"))\
                    #)

        #async with self._client.post(self.api_url, json = chain.to_dict()) as resp:
            #data = await resp.json()
            #print(data)
            #if data['data'] is None:
                #logger.warn(f"data is None, result = {data}")
                #return None
            #if data['data'] is None or data['data']['user'] is None:
                #return None
            #owners = []
            #followers = [Owner(node['login'], Owner.User) 
                         #for node in  data['data']['user']['followers']['nodes']]
            #print(f"followers = {followers}")

            #result = True
            #return result

    async def handle_org(self, org:Owner):
        def generate_chain():
            chain = Chain("user")\
                    (login = org.login)

            if has_more_members:
                chain = chain.get(Chain("members")\
                    (first = 10)\
                     .get(Chain("pageInfo")\
                         .get("endCursor hasNextPage"))\
                    .nodes\
                    .get("login"))

            if has_more_repos:
                chain = chain\
                    .get(Chain("repositories")\
                        (first = 10, after = repos_end_cursor)\
                         .get(Chain("pageInfo")\
                             .get("endCursor hasNextPage"))\
                        .nodes\
                         .get('name', 'url','description','updatedAt', 'projectsUrl', 'forkCount')\
                         .get(Chain("languages")
                              (first = 10)\
                              .nodes\
                              .get("name"))
                         .get(Chain("stargazers")\
                             (first = 1)\
                             .get("totalCount"))\
                         .get(Chain("watchers")\
                             (first = 1)\
                             .get("totalCount"))\
                        )

            return chain

        chain = Chain("organization")\
                (login = org.login)\
                .get(Chain("members")\
                    (first = 10)\
                     .get(Chain("pageInfo")\
                         .get("endCursor hasNextPage"))\
                    .nodes\
                    .get("login"))\
                .get(Chain("repositories")\
                    (first = 10)\
                     .get(Chain("pageInfo")\
                         .get("endCursor hasNextPage"))\
                    .nodes\
                     .get('name', 'url','description' , 'updatedAt', 'projectsUrl', 'forkCount')\
                     .get(Chain("languages")
                          (first = 10)\
                          .nodes\
                          .get("name"))
                     .get(Chain("stargazers")\
                         (first = 1)\
                         .get("totalCount"))\
                     .get(Chain("watchers")\
                         (first = 1)\
                         .get("totalCount"))\
                    )
        has_more_members = True
        has_more_repos = True
        while self._running :
            async with self._client.post(self.api_url, json = chain.to_dict()) as resp:
                raw_data = await resp.json()
                try:
                    if raw_data['data'] is None:
                        logger.warn(f"data is None, result = {raw_data}")
                        return None
                except KeyError:
                        global last_fail_time,fail_addition, min_fail_during
                        if  last_fail_time == 0:
                            last_fail_time = time.time()

                        now = time.time()
                        now_fail_during = now - last_fail_time
                        last_fail_time = now 
                        if now_fail_during < min_fail_during:
                            fail_addition += 5
                            min_fail_during = now_fail_during

                        during = random.randint(10, 20)
                        during += fail_addition
                        logger.warning(f"has abuse , sleep{during}, fail_addition = {fail_addition}, min_fail_during = {min_fail_during}, now_fail_during = {now_fail_during}")
                        logger.error(f"result = {raw_data}")
                        if "abuse" in raw_data['documentation_url'] :
                            during = random.randint(10, 20)
                            logger.warning(f"has abuse , sleep{during}")
                            time.sleep(during)
                            async with RateLimitWorker() as worker:
                                result = await worker.do()
                                logger.info(result)
                            return 
                data = raw_data['data']

                if has_more_members:
                    has_more_followers = data['organization']\
                            ['members']['pageInfo']['hasNextPage']
                    followers_end_cursor = data['organization']\
                            ['members']['pageInfo']['endCursor']
                    self.extract_owners(data['organization']\
                                        ['members']['nodes'], Owner.User)


                if has_more_repos:
                    has_more_repos = data['organization']\
                            ['repositories']['pageInfo']['hasNextPage']
                    repos_end_cursor = data['organization']\
                            ['repositories']['pageInfo']['endCursor']
                    self.extrack_repos(data['organization']\
                                       ['repositories']['nodes'])


            # no anymore data need to get
            if not (has_more_repos or has_more_members):
                logger.debug("no more data")
                break

            chain = generate_chain()

    async def hanle_unknown(self, owner:Owner):
        result = await self.handle_user(owner)
        if result is None:
            result = await self.handle_org(owner)
        return result

    async def fetch_data_from_user(self):
        owner = await self._q.get()
        if owner.type == Owner.User:
            result = await self.handle_user(owner)
        if owner.type == Owner.Org:
            result = await self.handle_org(owner)
        else:
            result = await self.hanle_unknown(owner)

async def run():
    queue = asyncio.Queue()
    await get_rate_limit()
    futs = [loop.create_task(fetch_users(chr(i))) for i in range(ord("a"), ord("a") + 1)]
    result = await asyncio.gather(*futs)
    logger.info(f"get users : {result}")
    #queue.put(Owner("google"))
    for i in result:
        for j in i:
            await queue.put(Owner(j))
    futs = [loop.create_task(fetch_data_from_user(queue)) for j in range(20)]
    result = await asyncio.gather( * futs)
    await get_rate_limit()

async def test():
    async with RateLimitWorker() as worker:
        result = await worker.do()
        logger.info(result)
    q = OwnerQueue()
    writer_owners = Writer("owner")
    writer_repos = Writer("repos")
    loop.create_task(writer_owners.run())
    loop.create_task(writer_repos.run())
    async with InitWorker(q) as worker:
        result = await worker.do()

    async with FetchWorker(q, writer_owners,  writer_repos) as worker:
        result = await worker.do()

    workers = [FetchWorker(q, writer_owners, writer_repos) for i in range(20)]

    try:
        fut = asyncio.gather(*[w.do() for w in workers])
        await fut
    except KeyboardInterrupt:
        exit()
    finally:
        for worker in workers:
            await worker._close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test())

