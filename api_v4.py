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
    "Authorization":"bearer 6d551a019223e4345e064de043d1fe46b9cd0260", 
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"
}
#sample  -  - 
{'query':'{ repository(owner: "octocat", name: "Hello-World") { pullRequest(number: 1) { commits(first: 10) { edges { node { commit { oid message } } } } comments(first: 10) { edges { node { body author { login } } } } reviews(first: 10) { edges { node { state } } } } } }'}
 #-  - 


get_rate_chain = Chain("rateLimit").get("cost limit remaining resetAt")
resp = Post("https://api.github.com/graphql", json =get_rate_chain.to_dict(), headers = header )
logger.info(resp.json())

search_chain = Chain("search")\
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


#owner_chain = Chain("repositoryOwner")\
        #(login = "3rf")\
        #.get(Chain("... on User").get(Chain("organizations")\
                                     #(first = 10)\
                                     #.nodes.get("login")))
             #(first = 10)\
             #.nodes\
            #.get("login"))

owner_chain = Chain("repositoryOwner")\
        (login = "3rf")\
        .get(Chain("... on User")\
             .get(Chain("organizations")\
                  (first = 10)\
                  .nodes.get("login")),Chain("... on Organization")\
             .get("login") )

#t = {'query': '{ repositoryOwner(login:"gh-impact"){ ... on User { login  }... on Organization{ login }}}'}
#t = {'query': '{ repositoryOwner(login:"3rf"){ ... on User { organizations(first:10){ nodes { login  } }}}}'}


#logger.info(search_chain.str())
#resp = Post("https://api.github.com/graphql", json =search_chain.to_dict(), headers = header )
#logger.info(resp.json())

logger.info(owner_chain.to_dict())
resp = Post("https://api.github.com/graphql", json =owner_chain.to_dict(), headers = header )
#resp = Post("https://api.github.com/graphql", json =t, headers = header )
logger.info(resp.json())

