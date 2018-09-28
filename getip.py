#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import time
import requests 
from requests import Session, Request, get
from bs4 import BeautifulSoup as Soup

class IP(object):
    def __init__(self, ip, port,rate = 0):
        self.ip = ip
        self.port = port


    def to_dict(self):
        return dict(https = self.ip + self.port)

    def __str__(self):
        return f"ip = {self.ip:<16}\tport = {self.port:<4}"


class IPPool(object):
    end_page = 5
    test_url = "https://github.com/"
    test_timeout = 10
    def __init__(self):
        pass

    def get_ips(self):
        l = []
        l.extend(self.get_360_ip())
        l.extend(self.get_Xi_ip())
        l.extend(self.get_Yun_ip())
        return l

    def get_360_ip(self):
        url = "http://www.swei360.com/free/?page="
        l = []
        for i in range(1, IPPool.end_page + 1):
            real_url = url + str(i)
            res = get(url)
            sp = Soup(res.text, "lxml")
            trs = sp.select("tbody tr")
            l.extend([IP(tr.select("td")[0].text, tr.select("td")[1].text)
             for tr in trs if tr.select("td")[3].text == "HTTPS"])
        print("360代理")
        for i in l:
            print(i)
        return l

    def get_Xi_ip(self):
        l = []

        return l

    def get_Yun_ip(self):
        url = "http://www.ip3366.net/free/?stype=1&page="
        l = []
        for i in range(1, IPPool.end_page + 1):
            real_url = url + str(i)
            res = get(url)
            sp = Soup(res.text, "lxml")
            trs = sp.select("tbody tr")
            l.extend([IP(tr.select("td")[0].text, tr.select("td")[1].text)
             for tr in trs if tr.select("td")[3].text == "HTTPS"])
        print("云代理")
        for i in l:
            print(i)
        return l



    def test(self):

        for ip in self.get_ips():
            start_time = time.time()
            try:
                res = get(IPPool.test_url, timeout = IPPool.test_timeout, proxies = ip.to_dict())
            except requests.exceptions.ProxyError as e :
                print("ProxyError")
                continue
            except requests.exceptions.ConnectTimeout as e:
                print("ConnectTimeout")
                continue
            else:
                end_time = time.time()
                req_time = end_time - start_time
                print(f"ip = {ip.ip}\tport = {ip.port}\ncode = {res.status_code}\tspend time = {req_time}")

if __name__ == "__main__":
    ip_pool = IPPool()



