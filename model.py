#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from logger import get_logger

logger = get_logger(__name__)

class Type(object):
    def __init__(self, str):
        self.str = str


class Chain(object):
    def __init__(self, name):
        self._path = f'{{ {name}}}'
        self._no_add = False
        self._start = self._path.index("}")

    def __getattr__(self, path):
        if(self._no_add):
            t = f' {path} '
        else:
            t = f'{{ {path} }}'
        idx = self._path.index("}",self._start)
        self._path = self._path[:idx] + t + self._path[idx:]

        if(self._no_add):
            self._start += len(t)
        else:
            self._path.index("}", self._start)

        self._no_add = False
        return self

    def _insert_chain(self, chain):
        t = chain.str_without_bracket()
        return t

    def get(self, *args):
        idx = self._path.index("}",self._start)
        if self._no_add:
            t = ""
            for i in args:
                if isinstance(i, Chain):
                    t += self._insert_chain(i)
                    continue
                t += f" {i} "
        else:
            t = " {"
            for i in args:
                if isinstance(i, Chain):
                    t += self._insert_chain(i)
                    continue
                t += f" {i} "
            t += " } "

        head = self._path[:idx]
        tail = self._path[idx:]
        self._path =  head + t + tail
        #print(f"t = {t}")
        #print(f"{head}  < this > {tail}")
        j = self._start
        if(self._no_add):
            self._start += len(t)
        else:
            delta = t.rindex("}")
            self._start += delta
            #self._start = self._path.index("}", self._start)
        head = self._path[:self._start]
        tail = self._path[self._start:]
        #print(f" next {head}  < this > {tail}")

        self._no_add = True
        return self

    def __call__(self, **kargs):
        t = "("
        for i, j in kargs.items():
            if isinstance(j, Type):
                t += f'{i}:{j.str},'
            elif isinstance(j, str):
                t += f'{i}:"{j}",'
            else:
                t += f'{i}:{j},'
        t = t[:-1] + ")"

        idx = self._path.index("}",self._start)
        self._path = self._path[:idx] + t + self._path[idx:]
        self._start += len(t)
        self._no_add = False
        return self
    def on1(self, Chain):
        pass


    def on(self, type):
        if(self._no_add):
            t = f" ... on {type} "
        else:
            t = f"{{ ... on {type} }}"

        idx = self._path.index("}",self._start)
        self._path = self._path[:idx] + t + self._path[idx:]
        #self._start += len(t) - 1
        if(self._no_add):
            self._start += len(t)
        else:
            delta = t.rindex("}")
            self._start += delta
            #self._path.index("}", self._start + 1)
        self._no_add = False
        return self

    def __str__(self):
        return(self._path)

    def to_dict(self):
        return {"query":self._path}

    def str(self):
        return self._path

    def str_without_bracket(self):
        t1 = self._path.index("{")
        t2 = self._path.rindex("}",self._start)
        #print(f"no is {self._path[t1 + 1:t2]}")
        return self._path[t1 + 1:t2 ]

def test():
    #c = Chain("search")
    #logger.debug(c(last = 10).get("repositoryCount").get("test")\
          #.get(Chain("star")(last = 4).get("test3")).on("type").attr)
    #chain = Chain("repositoryOwner")\
            #(login = "3rf")\
            #.on("User")\
            #.get(Chain("organizations")\
                 #(first = 10)\
                 #.nodes.get("f"))\
    #.get("first")

    #logger.info(Chain("first")(first = 3).to_dict())
    #logger.info(Chain("first")(first = 3).get("test").nodes.to_dict())
    #logger.info(Chain("first")(first = 3).nodes.get("f").to_dict())
    c = Chain("test")\
        .on("Repository")\
        .get(Chain("... on User")\
             .get("totalCount"))\
        .get(Chain("stargazers")\
             (last = 1).\
             get("totalCount"))
    logger.info(c.to_dict())
    #logger.info(Chain("test").get("test1").str_without_bracket())
    #logger.info(Chain("first")(first = 3).get(Chain("test").get("test1")).nodes.get("f").to_dict())

    #logger.info(Chain("first")(first = 3).nodes.get("f").get("g").to_dict())
    #logger.info(chain.to_dict())






if __name__ == "__main__":
    test()


