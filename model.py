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
        self._has_get = False
        self._start = self._path.index("}")

    def __getattr__(self, path):
        if(not self._has_get):
            t = f'{{ {path}}}'
        else:
            t = f' {path} '
        idx = self._path.index("}",self._start)
        self._path = self._path[:idx] + t + self._path[idx:]

        self._start += len(t)
        self._has_get = False
        return self

    def _insert_chain(self, chain):
        t = chain.str_without_bracket()
        return t

    def get(self, *args):
        idx = self._path.index("}",self._start)
        if self._has_get:
            t = " "
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
            t += " }"

        self._path = self._path[:idx] + t + self._path[idx:]
        if(self._has_get):
            self._start += len(t)
        else:
            self._start += len(t) - 1
        self._has_get = True
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

        idx = self._path.index("}",self._start)
        self._path = self._path[:idx] + t[:-1] + ")" + self._path[idx:]
        self._start += len(t)
        self._has_get = False
        return self

    def on(self, type):
        if(not self._has_get):
            t = f"{{ ... on {type}}}"
        else:
            t = f" ... on {type} "

        idx = self._path.index("}",self._start)
        self._path = self._path[:idx] + t + self._path[idx:]
        self._start += len(t) - 1
        self._has_get = False
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
        return self._path[t1 + 1:t2]

def test():
    c = Chain("search")
    logger.debug(c(last = 10).get("repositoryCount").get("test")\
          .get(Chain("star")(last = 4).get("test3")).on("type").attr)



if __name__ == "__main__":
    test()

