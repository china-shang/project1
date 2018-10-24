#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import glob
import json


fs = glob.iglob("repo*")

data = []
for i in fs:
    with open(i) as fp:
        t = json.load(fp)
        data.extend(t)
all1 = len(data)
print(all1)
data_set = {i['projectsUrl'] for i in data}
all2 = len(data_set)
print(all2)
repeat_rate = (all1 - all2) / all1
print(f"repeat_rate = {repeat_rate}")

        


