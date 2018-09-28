#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import requests 
from requests import Session, Request, get as Get
from bs4 import BeautifulSoup as Soup


for i in "abcdefgh":
    for page in range(20):
        resp = Get(f"https://gitee.com/search?page={page}&q={i}&sort=watches_count&type=")
        sp = Soup(resp.text, "lxml")
        print(f"title = {sp.title.text}")




