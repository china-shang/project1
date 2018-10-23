#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import time
import json

class Writer(object):
    _save_deadline = 1000

    def __init__(self,name = None):
        self._running = True
        if name:
            self.file_name = name
        else:
            self.file_name = ""
        self._data = []

    def add_data(self, l:list):
        self._data.extend(l)

    def size(self):
        return len(self._data)

    def clear(self):
        self._data = []

    def write(self):
        name = self.file_name + str(int(time.time() * 1000))
        with open(name,  "w") as fp:
            json.dump(self._data, fp)
        #print("has write")

    async def run(self):
        while self._running:
            #print("in run")
            if self.size()  >= self._save_deadline:
                self.write()
                self.clear()
            else:
                await asyncio.sleep(1)
            #print(self._data)

async def adder(w):
    while True:
        await asyncio.sleep(0.3)
        w.add_data([2, 3])

async def test():
    writer = Writer()
    writer.add_data(["sdjf", "sdjf"])
    loop.create_task(adder(writer))
    await writer.run()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test())



