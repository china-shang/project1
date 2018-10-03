#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from requests import Session,Request, get as Get, post as Post
from requests.exceptions import  * 
import requests
import json
import time
import queue
import logging
from logger import get_logger
from model import Chain, Type
import threading


logger = get_logger(__name__)

header = {
    "Authorization":"bearer f9ae98acf445d8bf8b1067551563e901bdb7f476"
}

data = {
    "query":"query{viewer{login}}"
}
data = {'query':'{ repository(owner: "octocat", name: "Hello-World") { pullRequest(number: 1) { commits(first: 10) { edges { node { commit { oid message } } } } comments(first: 10) { edges { node { body author { login } } } } reviews(first: 10) { edges { node { state } } } } } }'}

def generate_query(data):
    return {"query":data}
data = '{search(type: REPOSITORY, query: "t sort:forks", first:10) { nodes { ... on Repository{forkCount watchers(last:1){totalCount}stargazers(last:1){totalCount} }} repositoryCount }}'

data1 = '{rateLimit{cost limit remaining resetAt}}'

chain = Chain("search")\
        (type = Type("REPOSITORY"), query = "a sort:forks", first = 100)\
        .get("repositoryCount")\
        .get(Chain("pageInfo")\
             .get("endCursor"))\
        .nodes\
        .on("Repository")\
        .get("forkCount")\
        .get(Chain("watchers")\
             (last = 1).\
             get("totalCount"))\
        .get(Chain("stargazers")\
             (last = 1).\
             get("totalCount"))
print("chain = " , chain.to_dict())

logger.info(generate_query(data))
generate_query(data)
resp = Post("https://api.github.com/graphql", json =generate_query(data1), headers = header )
print(chain.to_dict())
resp = Post("https://api.github.com/graphql", json =chain.to_dict(), headers = header )

logger.info(resp.json())
