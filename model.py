#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

    def _get_chain(self, chain):
        t = chain.str_no()
        idx = self._path.index("}",self._start)
        self._path = self._path[:idx] + t + self._path[idx:]

        self._has_get = True
        self._start += len(t) 

        return self

    def get(self, *args):
        if type(args[0]) is Chain:
            self._get_chain(args[0])
            return self

        idx = self._path.index("}",self._start)
        if self._has_get:
            t = " "
            for i in args:
                #if type(i) is Chain:
                    #self._get_chain(i)
                    #continue
                t += f" {i} "
        else:
            t = " {"
            for i in args:
                #if type(i) is Chain:
                    #self._get_chain(i)
                    #continue
                t += f" {i} "
            t += " }"

        self._path = self._path[:idx] + t + self._path[idx:]
        if(not self._has_get):
            self._start += len(t) - 1
        else:
            self._start += len(t)
        self._has_get = True
        return self

    def __call__(self, **kargs):
        t = "("
        for i, j in kargs.items():
            if type(j) is Type:
                t += f'{i}:{j.str},'
            elif type(j) is str:
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

    def str_no(self):
        t1 = self._path.index("{")
        t2 = self._path.rindex("}",self._start)
        return self._path[t1 + 1:t2]

if __name__ == "__main__":

    c = Chain("search")
    print(c(last = 10).get("repositoryCount").get("test")\
          .get(Chain("star")(last = 4).get("test3")).on("type").attr)

