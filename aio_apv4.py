#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import time
import random
import queue
import logging
from logger import get_logger
from aiohttp import ClientSession 
import threading
import aiohttp
import asyncio
import itertools
from aio_mysql_client import  * 

from model import Chain, Type
from aio_writer import Writer
from aio_model import  * 
from baseuser import BaseUser

with open("token.json") as fp:
    key = json.load(fp)


class Statist(object):

    def __init__(self):
        self.all_repo = 0
        self.all_user = 0

        self.start_time = time.time()
        self.last_fail_time = 0

        self.repos_from_fail = 0
        self.user_from_fail = 0
        self.fail_cnt = 0
        self.max_fail_interval = 0
        self.min_fail_interval = 0

        self.req_count = 0

    def increase_repos(self, num = 1):
        self.all_repo += num

    def increase_user(self, num = 1):
        self.all_user += num

    def increase_req(self, num = 1):
        self.req_count += num

    def get_avg_speed(self):
        now = time.time()
        cost = now - self.start_time
        result = (self.all_repo / cost, self.all_user / cost, self.req_count / cost)
        return result

    def get_recent_speed(self, sleep_during = 0):
        if self.last_fail_time == 0:
            return self.get_avg_speed()

        now = time.time()
        cost = now - self.last_fail_time - sleep_during
        result = (self.repos_from_fail / cost, self.user_from_fail / cost, self.req_count / cost)
        return result

    def get_cost_time(self):
        cost = now - self.start_time
        return cost

    def record_error(self):
        now = time.time()
        interval = now - self.last_fail_time
        self.max_fail_interval = max(interval, self.max_fail_interval)
        self.min_fail_interval = min(interval, self.min_fail_interval)

        self.fail_cnt += 1
        self.last_fail_time = now

class Session(ClientSession):
    statist = None

    def __init__(self, *args, **xargs):
        super().__init__(*args, **xargs)

    #async def get(self, *args, **kargs):
        #self.statist.increase_req()
        #t = await super().get(*args, **kargs)
        #return t

    #async def post(self, *args, **kargs):
        #self.statist.increase_req()
        #t = await super().post(*args, **kargs)
            
        #print(type(t))
        #return t

    async def _request(self, *args, **kargs):
        Session.statist.increase_req()
        logger.debug(f"{self.statist.get_avg_speed()[2]:.2f}")
        _, _, rate = self.statist.get_avg_speed()
        if rate > 1.0:
            expect_time = self.statist.req_count / 1.0
            during = time.time() - self.statist.start_time
            sleep_time = (expect_time - during) * 1.1
            logger.warning(f"overspeed , then sleep {sleep_time}")
            await asyncio.sleep(sleep_time)
        return await super()._request(*args, **kargs)


class AbuseHander(object):
    rate_deadline = 2
    def __init__(self, statist:Statist):
        self.statist = statist
        self._addition = 0

    def handle_abuse(self):
        if self.is_same_abuse():
            pass

        self.statist.record_error()
        now = time.time()
        fail_interval = now - self.statist.last_fail_time
        if fail_interval < self.statist.min_fail_interval:
            self.fail_addition += 5
            AbuseHander.rate_deadline *= 0.95
            AbuseHander.rate_deadline  = max(0.13, FetchWorker.rate_deadline)
            logger.warning(f"rate decrease to {FetchWorker.rate_deadline:.2f}")

        during = random.randint(30, 55)
        during += fail_addition
        logger.warning(f"tirgger abuse , sleep{during}, fail_addition = {fail_addition}, min_fail_during = {min_fail_during}, now_fail_during = {now_fail_during}")
        time.sleep(during)

    def handle_overspeed(self, rate):
        if rate > self.rate_deadline:
            logger.info(f"rate {rate} > rate_deadline {self.rate_deadline}, pausing {during:.2f}")
            time.sleep(during)
        if rate > self.rate_deadline * 1.2:
            self.pool.decrease_worker()
        if rate < self.rate_deadline * 0.8:
            self.pool.increase_worker()

    def is_same_abuse(self):
        pass

logger = get_logger(__name__)
logger.setLevel(logging.DEBUG)

get_rate_chain = Chain("rateLimit").get("cost limit remaining resetAt")

async def fetch_users(q):
    search_user_chain = Chain("search")\
            (type = Type("REPOSITORY"), query = f"{q} sort:forks", first = 100)\
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
            (login = user.name)\
            .get(Chain("followers")\
                (first = 100)\
                 .get(Chain("pageInfo")\
                     .get("endCursor hasNextPage"))\
                .nodes\
                .get("login"))\
            .get(Chain("following")\
                (first = 10)\
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
            (login = org.name)\
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

async def fetch_data(q:asyncio.Queue):
    try:
        owner = await q.get()
    except LackUser:
        owner = await q.get(True)
        self._fetch_users = True

    if owner.type == Owner.User:
        result = await handle_user(owner)
    if owner.type == Owner.Org:
        result = await handle_org(owner)
    else:
        result = await hanle_unknown(owner)

    logger.info(f"{owner.name}:{result['data']}")

class Worker(object):
    header = {
        "Authorization":f"bearer  {key['key']}", 
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"
    }
    api_url = "https://api.github.com/graphql"

    def __init__(self):
        self._client = Session( headers = Worker.header, timeout = aiohttp.ClientTimeout(total = 60))
        self._running = True

    async def do(self):
        pass

    async def _close(self):
        await self._client.close()

    def pause(self):
        self._running = False
        asyncio.ensure_future(self._client.close())

    def restart(self):
        self._running = True
        self._client = Session(headers = Worker.header, timeout = aiohttp.ClientTimeout(total = 60))
        asyncio.ensure_future(self.do())

    async def __aenter__(self):
        if self._client.closed:
            self._client = Session(headers = Worker.header)
        return self

    async def __aexit__(self, exe_type, exc_value, traceback):
        self._running = False
        await self._close()

class RateLimitWorker(Worker):
    def __init__(self):
        super().__init__()
        self._chain = Chain("rateLimit").get("cost limit remaining resetAt")

    async def do(self):
        async with self._client.post(self.api_url,json = self._chain.to_dict()) as resp:
            pass
        resp = await  self._client.post(self.api_url,json = self._chain.to_dict()) 
        async with resp:
            print(f"api_url = {self.api_url}")
            result = await resp.json()
            print(result)
            return result['data']

class InitWorker(Worker):
    def __init__(self, q:DBClient):
        super().__init__()
        self._q = q
        self._writer = Writer()

    async def do(self):
        owners = await self._do("a")
        for i in owners:
            self._q.put(BaseUser(i))

    async def _do(self,q = "q"):
        chain = Chain("search")\
                (type = Type("REPOSITORY"), query = f"{q} sort:forks", first = 100)\
                .nodes\
                .on("Repository")\
                .get(Chain("owner").get("login"))
        async with self._client.post(self.api_url, json =chain.to_dict() ) as resp:
            result = await resp.json()
            names = [node['owner']['login'] for node in result['data']['search']['nodes'] ]
            logger.info(f"names = {names}")
            return names

class FetchWorker(Worker):
    rate_deadline = 0.4
    def __init__(self, q:asyncio.Queue,statist:Statist, writer_owners, writer_repos,  name = "", num = -1, pool = None):
        super().__init__()
        if len(name) > 1:
            self.name = name
        else:
            self.name = f"worker{num}"

        self._fetch_users = False
        self._q = q
        self.statist = statist
        self.pool = pool
        self._writer_repos = writer_repos
        self._writer_owners = writer_owners

    def handle_abuse(self):
        pass
        #global last_fail_time,fail_addition, min_fail_during, count1, start_time
        #now = time.time()
        #now_fail_during = now - last_fail_time
        #last_fail_time = now 

        #if now_fail_during < min_fail_during:
            #fail_addition += 5
        #FetchWorker.rate_deadline *= 0.95
        #FetchWorker.rate_deadline  = max(0.13, FetchWorker.rate_deadline)


        #logger.warning(f"rate decrease to {FetchWorker.rate_deadline:.2f}")
        #min_fail_during = min(now_fail_during, min_fail_during)

        #during = random.randint(30, 55)
        #during += fail_addition
        #logger.warning(f"has abuse , sleep{during}, fail_addition = {fail_addition}, min_fail_during = {min_fail_during}, now_fail_during = {now_fail_during}")
        #time.sleep(during)
        #count1 = 0
        #start_time = time.time()

    async def do(self):
        self.this = 0
        while self._running:
            v1, v2, v3 = self.statist.get_avg_speed()
            logger.info(f"repos rate = {v1:.2f}, user rate = {v2:.2f},req rate = {v3:.2f}")
            await self._do()

            if v3 < 0.8:
                self.pool.increase_worker()

            if v3 > 1.1:
                self.pool.decrease_worker()

    async def _do(self):
        try:
            await self.fetch_data()
            self.statist.increase_user()
        except (asyncio.TimeoutError, aiohttp.ServerConnectionError):
            logger.warning("execept Exception")
            await asyncio.sleep(3)

    def overspeed(self, rate):
        pass

    def extrack_repos(self, repos:list):
        count = len(repos)
        self.statist.increase_repos(count)
        #logger.info(f"get repos:{repos}")
        self._writer_repos.add_data(repos)
        logger.info(f"add repos:{count} from {self.owner.name} all has {self.statist.all_repo}")
        
    def extract_owners(self, owners, type = Owner.Unkonwn):
        if type == Owner.Org:
            is_org = True
        else:
            is_org = False
        owners = [BaseUser(i["login"],is_org ) for i in owners )]
        #self._writer_owners.add_data(owners)
        #logger.info(f"get owners:{owners} from {self.owner.name}")
        for i in owners:
            self._q.put(i)

        #logger.info(f"{self.name}:  add {len(owners)} from {self.owner.name}")

    async def handle_user(self, user:Owner):
        def gen_chain(init = False):
            if init:
                chain = Chain("user")\
                        (login = user.name)\
                        .get(Chain("followers")\
                            (first = 10)\
                             .get(Chain("pageInfo")\
                                 .get("endCursor hasNextPage"))\
                            .nodes\
                            .get("login"))\
                        .get(Chain("following")\
                            (first = 10)\
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
                            (first = 100)\
                             .get(Chain("pageInfo")\
                                 .get("endCursor hasNextPage"))\
                            .nodes\
                             .get('name', 'url','description','updatedAt', 'projectsUrl', 'forkCount')\
                             .get(Chain("languages")
                                  (first = 100)\
                                  .nodes\
                                  .get("name")))
                return chain


            chain = Chain("user")\
                    (login = user.name)
            chain = gen_chain(init = True)
            if has_more_followers:
                chain = chain\
                    .get(Chain("followers")\
                        (first = 10, after = followers_end_cursor )\
                         .get(Chain("pageInfo")\
                             .get("endCursor hasNextPage"))\
                        .nodes\
                        .get("login"))

            if has_more_following:
                chain = chain\
                    .get(Chain("following")\
                        (first = 10, after = following_end_cursor)\
                         .get(Chain("pageInfo")\
                             .get("endCursor hasNextPage"))\
                        .nodes\
                        .get("login"))

            if has_more_repos:
                chain = chain\
                    .get(Chain("repositories")\
                        (first = 100, after = repos_end_cursor)\
                         .get(Chain("pageInfo")\
                             .get("endCursor hasNextPage"))\
                        .nodes\
                         .get('name', 'url','description','updatedAt', 'projectsUrl', 'forkCount')\
                         .get(Chain("languages")
                              (first = 100)\
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

        has_more_followers = True
        has_more_following = True
        has_more_orgs = True
        has_more_repos = True
        if not self._fetch_users:
            has_more_followers = False
            has_more_following = False
            has_more_orgs = False

        chain = gen_chain(init = True)
        while self._running :
            async with self._client.post(self.api_url, json = chain.to_dict()) as resp:
                print(self.statist.get_avg_speed())
                try:
                    raw_data = await resp.json()
                    if raw_data['data'] is None:
                        logger.warn(f"data is None, result = {raw_data}")
                        return None
                    if raw_data['data']['user'] is None:
                        return False
                    data = raw_data['data']
                except KeyError:
                    logger.error(f"result = {raw_data}")
                    if "abuse" in raw_data['documentation_url'] :
                        self.handle_abuse()
                        return  None
                except Exception :
                    logger.error(f"result = {raw_data}")


                #if has  % 20 == 0:
                    #global count, count1
                    #count1 += 1
                    #count += 1
                    #await asyncio.sleep(3)

                #if has  % 10 == 0:
                    #await asyncio.sleep(1)

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
                logger.debug(f"{self.owner.name}no more data")
                break

            chain = gen_chain()
        return True

    async def handle_org(self, org:Owner):
        def gen_chain(init = False):
            if init:
                chain = Chain("organization")\
                        (login = org.name)\
                        .get(Chain("members")\
                            (first = 100)\
                             .get(Chain("pageInfo")\
                                 .get("endCursor hasNextPage"))\
                            .nodes\
                            .get("login"))\
                        .get(Chain("repositories")\
                            (first = 100)\
                             .get(Chain("pageInfo")\
                                 .get("endCursor hasNextPage"))\
                            .nodes\
                             .get('name', 'url','description' , 'updatedAt', 'projectsUrl', 'forkCount')\
                             .get(Chain("languages")
                                  (first = 100)\
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
                    (login = org.name)

            if has_more_members:
                chain = chain.get(Chain("members")\
                    (first = 100, after = members_end_cursor)\
                     .get(Chain("pageInfo")\
                         .get("endCursor hasNextPage"))\
                    .nodes\
                    .get("login"))

            if has_more_repos:
                chain = chain\
                    .get(Chain("repositories")\
                        (first = 100, after = repos_end_cursor)\
                         .get(Chain("pageInfo")\
                             .get("endCursor hasNextPage"))\
                        .nodes\
                         .get('name', 'url','description','updatedAt', 'projectsUrl', 'forkCount')\
                         .get(Chain("languages")
                              (first = 100)\
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

        has_more_members = True
        has_more_repos = True
        if not self._fetch_users:
            has_more_members = False
        chain = gen_chain(init = True)
        while self._running :
            async with self._client.post(self.api_url, json = chain.to_dict()) as resp:
                print(self.statist.get_avg_speed())
                raw_data = await resp.json()
                try:
                    if raw_data['data'] is None:
                        logger.warn(f"data is None, result = {raw_data}")
                        return None
                except KeyError:
                    logger.error(f"result = {raw_data}")
                    if "abuse" in raw_data['documentation_url'] :
                        self.handle_abuse()
                        return None
                data = raw_data['data']
                if not 'organization' in data:
                    logger.error(f"KeyError data = {data}")
                    return 

                #if has  % 5 == 0:
                    #await asyncio.sleep(3)
                
                #if has  % 20 == 0:
                    #global count, count1
                    #count1 += 1
                    #count += 1
                    #await asyncio.sleep(3)

                if has_more_members:
                    has_more_members = data['organization']\
                            ['members']['pageInfo']['hasNextPage']
                    members_end_cursor = data['organization']\
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
                logger.debug(f" {self.owner.name} no more data")
                break

            chain = gen_chain()

    async def hanle_unknown(self, owner:Owner):
        result = await self.handle_user(owner)
        if result is None:
            return 
        if not result:
            result = await self.handle_org(owner)
        return result

    async def fetch_data(self):
        try:
            self.owner = await self._q.get()
            self._fetch_users = False
        except LackUser:
            logger.warning("no task , fetch more user")
            self.owner = await self._q.get(True)
            self._fetch_users = True

        owner = self.owner
        logger.info(f"{self.name}: get Task ")
        #if not owner.is_org:
            #result = await self.handle_user(owner)
        if owner.is_org:
            result = await self.handle_org(owner)
        else:
            result = await self.hanle_unknown(owner)
        self._q.complete(owner, self._fetch_users)

class WorkerPool(object):
    def __init__(self, q,statist, writer_owners, writer_repos, size = 1):
        self.f = asyncio.Future()
        self.size = size
        self.now = 0
        self._active = []
        self.w_owner = writer_owners
        self.w_repos = writer_repos
        self.q = q
        self.statist = statist

        self._inactive = []

    def start(self):
        workers = [FetchWorker(self.q,self.statist,  self.w_owner, self.w_repos, num = i, pool = self) for i in range(self.size)]
        fut = asyncio.gather(*[w.do() for w in workers])
        asyncio.ensure_future(fut)
        self._active = workers
        self.now = len(self._active)

    def increase_worker(self):
        if self.now >= self.size :
            return 
        worker = self._inactive.pop()
        self._active.append(worker)
        self.now = len(self._active)
        worker.restart()
        logger.info(f"increase worker now has {self.now} workers")

    def decrease_worker(self):
        if self.now <= 0:
            return 
        worker = self._active.pop()
        self._inactive.append(worker)
        self.now = len(self._active)
        worker.pause()
        logger.info(f"decrease worker now has {self.now} workers")
    async def done(self):
        await self.f

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
    futs = [loop.create_task(fetch_data(queue)) for j in range(20)]
    result = await asyncio.gather( * futs)
    await get_rate_limit()

def save_queue(q:OwnerQueue):
    prefix = "queue.data"
    file_name = prefix + str(int(time.time() * 1000))
    logger.info("start save queue")
    with open(file_name, "w") as fp:
        fp.writelines([s + "\n" for s in q._set])
    logger.info("end save queue")


#async def test():
    #async with RateLimitWorker() as worker:
        #result = await worker.do()
        #logger.info(result)
    #q = OwnerQueue()
    #writer_owners = Writer("owner")
    #writer_repos = Writer("repos")
    #loop.create_task(writer_owners.run())
    #loop.create_task(writer_repos.run())
    #async with InitWorker(q) as worker:
        #result = await worker.do()

    #async with FetchWorker(q, writer_owners,  writer_repos) as worker:
        #result = await worker.do()

    #workers = [FetchWorker(q, writer_owners, writer_repos, num = i) for i in range(4)]

    #try:
        #fut = asyncio.gather(*[w.do() for w in workers])
        #await fut
    #except KeyboardInterrupt:
        #pass
    #finally:
        #for worker in workers:
            #await worker._close()
        #save_queue(q)
async def test():
    statist = Statist()
    Session.statist = statist

    async with RateLimitWorker() as worker:
        result = await worker.do()
        logger.info(result)
    #q = OwnerQueue()
    q = DBClient("0.0.0.0", 8080)
    async with InitWorker(q) as worker:
        result = await worker.do()

    #await asyncio.sleep(10)
    writer_owners = Writer("owner")
    writer_repos = Writer("repos")
    loop.create_task(writer_owners.run())
    loop.create_task(writer_repos.run())
    #async with InitWorker(q) as worker:
        #result = await worker.do()
    pool = WorkerPool(q,statist, writer_owners, writer_repos, 6)
    pool.start()

    await pool.done()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test())
    #test


