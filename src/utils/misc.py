#!/usr/bin/python3
# -*- coding: utf-8 -*-
from past.builtins import xrange


def chunkify(lst,n):
    return [lst[i::n] for i in xrange(n)]