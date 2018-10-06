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
    "Authorization":"bearer 148bc2df28a4ca89d04fe46c6fc156f48b4c12dc"
}
data = {'query':'{ repository(owner: "octocat", name: "Hello-World") { pullRequest(number: 1) { commits(first: 10) { edges { node { commit { oid message } } } } comments(first: 10) { edges { node { body author { login } } } } reviews(first: 10) { edges { node { state } } } } } }'}


get_rate_chain = Chain("rateLimit").get("cost limit remaining resetAt")
resp = Post("https://api.github.com/graphql", json =get_rate_chain.to_dict(), headers = header )
logger.info(resp.json())

chain = Chain("search")\
        (type = Type("REPOSITORY"), query = "a sort:forks", first = 100)\
        .get("repositoryCount")\
        .get(Chain("pageInfo")\
             .get("endCursor"))\
        .nodes\
        .on("Repository")\
        .get("forkCount", Chain("watchers")\
             (last = 1).\
             get("totalCount"))\
        .get(Chain("stargazers")\
             (last = 1).\
             get("totalCount"))

resp = Post("https://api.github.com/graphql", json =chain.to_dict(), headers = header )
logger.info(resp.json())
