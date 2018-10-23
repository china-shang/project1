#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
from aiohttp import web
from baseuser import  * 
from aio_mysql import  * 

from logger import get_logger
import logging

logger = get_logger(__name__)
logger.setLevel(logging.DEBUG)


class Server(object):
    def __init__(self, pool:QueuePool):
        self.pool = pool

    async def start(self):
        await self.pool.create_pool()
        asyncio.ensure_future(self.pool.update())

    async def put(self, request):
        #for i, j in request.query.items():
            #logger.debug(i, j)
        data = await request.json()
        for i in data:
            self.pool.put_user(BaseUser(i['name'], i['is_org']))
        logger.debug(f"put{data}")
        resp = web.Response(text=json.dumps({"status":"success"}), content_type = "application/json")
        return resp

    async def complete(self, req):
        data = await req.json()
        logger.debug(data)
        for i in data:
            logger.debug(f"complete = {i}")
            self.pool.complete(i[0],i[1])
        resp = web.Response(text=json.dumps({"status":"success"}), content_type = "application/json")
        return resp

    async def get(self, req):
        data = await req.json()
        logger.debug(data)
        produce = data['produce']
        users = await self.pool.get_users(produce)
        text = user_dumps({"status":"success","produce":produce,  "data":list(users)})
        resp = web.Response(text=text, content_type = "application/json")

        return resp

async def test():
    t = Server(QueuePool())
    await t.start()

    app = web.Application()
    app.add_routes([web.post('/put', t.put), 
                   web.get("/get", t.get), 
                   web.post("/complete", t.complete)])

    runner = web.AppRunner(app)
    await runner.setup()
    svr = web.TCPSite(runner, "0.0.0.0", 8080)
    await svr.start()

    logger.info("has start")
    await asyncio.sleep(1000)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test())


