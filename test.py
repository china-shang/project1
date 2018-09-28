#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import requests 
from requests import Session, Request, get as Get
from bs4 import BeautifulSoup as Soup

def f(a = 3):

    def g():
        g_var = "this is g_var"
        def k():
            k_var = "this is k_var"

    print(g_var, k_var)
f()
