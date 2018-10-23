#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import functools

class BaseUser(object):
    def __init__(self, name = "", is_org = False):
        self.name = name
        self.is_org = is_org

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if isinstance(other, str):
            return self.name == other
        if isinstance(other, BaseUser):
            return self.name == self.name
        return False
    def __str__(self):
        return f"BaseUser:{self.name}"
    
    def __repr__(self):
        return f"BaseUser:{self.name}"

class BaseUserEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, BaseUser):
            return {"name":obj.name, "is_org":obj.is_org}
        return json.JSONEncoder.default(self, obj)

class BaseUserDecoder(json.JSONDecoder):
    def decode(self, s):
        d = json.JSONDecoder.decode(s)
        return BaseUser(d['name'], d['is_org'])

user_dumps = functools.partial(json.dumps, cls = BaseUserEncoder )
user_loads = functools.partial(json.loads, cls = BaseUserDecoder)

def test():
    s = set([BaseUser("123")])
    s.add("123")
    print(s)

