#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import requests 
import time
from requests import Session, Request
from bs4 import BeautifulSoup as Soup
import t

session = Session()
ip_url = "http://www.xicidaili.com/wn/2"
header = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0', 'Accept-Encoding': 'gzip, deflate', 'Accept': '*/*', 'Connection': 'keep-alive'}

req = Request("GET",ip_url,headers = header)
res = session.send(req.prepare())

ip_pool = t.IPPool()
ip_pool.update_ip()

for i in range(ip_pool.ip_count()):
    ip = ip_pool.get_ip()
    start = time.time()
    try:
        res = requests.get("https://github.com",timeout = 10,  proxies = dict(https = ip.ip + ":" + str(ip.port)))

    except requests.exceptions.ProxyError as e :
        print("ProxyError")
        continue
    except requests.exceptions.ConnectTimeout as e:
        print("ConnectTimeout")
        continue
    end = time.time()
    print("speed time: %.2f" %(end - start), "code = ", res.status_code, "ip = ", ip.ip)
    


sys.exit()


#print(res.text)
#sp = Soup(res.text, "lxml")
#print("title:",sp.title )
#trs = sp.select("tr.") 

proxys = {
    #"http":"60.208.32.201:80", 
    #"https":"60.12.218.119:90", 
    #"https":"106.14.47.5:80"
    "https":"121.69.3.210:33468"
}

start = time.time()
res = requests.get("https://github.com", proxies = proxys)
end = time.time()
print("speed time: %.2f" %(end - start), "code = ", res.status_code)

