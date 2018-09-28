#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import time
import requests 
from requests import Session, Request
from bs4 import BeautifulSoup as Soup
t = ""

class IP(object):
    def __init__(self, tr):
        #print(tr)
        global t
        t = tr
        tds = tr.select("td")
        if(tr.select_one(".country img") is None):
            self.contry = ""
        else:
            self.contry = tr.select_one("img")['alt']
        self.ip = tds[1].text
        self.port = int(tds[2].text)
        if(tds[3].select_one("a") is None):
            self.addr = ""
        else:
            self.addr = tds[3].select_one("a").text
        self.type = tds[4].text
        self.proto = tds[5].text
        self.rate = float(tds[6].select_one("div")['title'][:-1])
        self.con_rate = float(tds[7].select_one("div")['title'][:-1])
        self.valid_during = tds[8].text
        self.test_time = tds[9].text
        self.fail_count = 0
        
        self.used = False

    def update(self, other):
        self.type = other.type
        self.proto  = other.proto
        self.rate  = other.rate
        self.con_rate  = other.con_rate
        self.valid_during  = other.valid_during
        self.test_time  = other.test_time
        self.fail_count  = other.fail_count

    def get_score(self) ->float:
        return  -(self.rate + self.con_rate / 2) * (self.fail_count + 1)

    def __str__(self) ->str:
        s = f"ip = {self.ip:<16}\tport = {self.port:<4}\trate = {self.rate:<4.2f}\tcon_rate = {self.con_rate:<4.2f}\tscore = {self.get_score():<4.2f}"
        return s

    def __eq__(self, other) -> bool:
        return self.ip == other.ip and self

    def __hash__(self):
        t = [int(i) for i in self.ip.split(".")]
        t.append(self.port)
        return hash(frozenset(t))

class IPPool(object):
    pages = 3
    def __init__(self):
        self._ips = []
        self._url = "http://www.xicidaili.com/wn/"
        header = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0',
                  'Accept-Encoding': 'gzip, deflate',
                  'Accept': '*/*',
                  'Connection': 'keep-alive'}

        req = Request("GET",self._url,headers = header)
        self._pre_request = req.prepare()

    def update_ip(self):
        session = Session()
        for i in range(1, self.pages + 1):
            self._pre_request.url = self._url + str(i)
            res = session.send(self._pre_request)
            self._handle_res(res)
        self._ips.sort(key = lambda x:x.get_score(), reverse = True)
        for i in self._ips:
            print(i)

    def _handle_res(self, res):
        #print(res.text)
        sp = Soup(res.text, "lxml")
        #print("title:",sp.title )
        trs = sp.select("tr.") 
        for tr in trs:
            t = IP(tr)
            if(t.type == "透明"):
                continue
            if(t in self._ips):
                self._ips[self._ips.index(t)].update(t)
            else:
                self._ips.append(t)

    def get_ip(self) ->IP:
        for i in self._ips:
            if(not i.used):
                i.used = True
                return i
        else:
            #print("no ip, start update")
            self.update_ip()
    def ip_count(self)->int:
        return len(self._ips)


if __name__ == "__main__":
    ip_pool = IPPool()
    ip_pool.update_ip()


