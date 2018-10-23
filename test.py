#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import requests 
from requests import Session, Request, get as Get
from bs4 import BeautifulSoup as Soup

def gen_body1():
    name = "name"
    is_org = True
    values = ""
    for i in range(4):
        values = f"{values}('{name}', '{is_org}'),"
    values = values[:-1]

    body = f"INSERT INTO git_owner (name,is_org) VALUES {values}"


    return body


def test():
    print(gen_body1())

def f2():
    f1()

def f1():
    pass


class A(B):
    def f():
        B.test()

class B:
    def test():
        pass



if __name__ == "__main__":
    test()
    f2()
    a = A()
    a.f()
