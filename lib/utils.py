#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: utils.py
# Date: Thu Dec 25 10:11:21 2014 +0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>

import sys
import time

def ensure_bin_str(s):
    if type(s) == str:
        return s
    if type(s) == unicode:
        return s.encode('utf-8')

def ensure_unicode(s):
    if type(s) == str:
        return s.decode('utf-8')
    if type(s) == unicode:
        return s

class ProgressReporter(object):
    """report progress of long-term jobs"""
    _start_time = None
    _prev_report_time = 0
    _cnt = 0
    _name = None
    _total = None

    def __init__(self, name, total=0, fout=sys.stderr):
        self._start_time = time.time()
        self._name = name
        self._total = int(total)
        self._fout = fout

    @property
    def total_time(self):
        return time.time() - self._start_time

    def trigger(self, delta=1, extra_msg='', target_cnt=None):
        if target_cnt is None:
            self._cnt += int(delta)
        else:
            self._cnt = int(target_cnt)
        now = time.time()
        if now - self._prev_report_time < 0.5:
            return
        self._prev_report_time = now
        dt = now - self._start_time
        if self._total and self._cnt > 0:
            eta_msg = '{}/{} ETA: {:.2f}'.format(self._cnt, self._total,
                    (self._total-self._cnt)*dt/self._cnt)
        else:
            eta_msg = '{} done'.format(self._cnt)
        self._fout.write(u'{}: avg {:.3f}/sec'
                         u', passed {:.3f}sec, {}  {} \r'.format(
            self._name, self._cnt / dt, dt, eta_msg, extra_msg))
        self._fout.flush()

    def finish(self):
        """:return: total time"""
        self._fout.write('\n')
        self._fout.flush()
        return self.total_time



import multiprocessing
from multiprocessing import Process, Queue
from collections import deque
import inspect
import dill
class PickleableMethodProxy(object):
    def __init__(self, func):
        self.data = dill.dumps(func)
        return
        assert inspect.ismethod(func)
        self.im_self = func.im_self
        self.method_name = func.__name__

    def __call__(self, *args, **kwargs):
        return dill.loads(self.data)(*args, **kwargs)
        return getattr(self.im_self, self.method_name)(*args, **kwargs)


def ensure_pickleable_func(func):
    if inspect.ismethod(func):
        return PickleableMethodProxy(func)
    return func

def pimap(map_func, iterator, nr_proc=None, nr_precompute=None):
    '''parallel imap'''
    map_func = ensure_pickleable_func(map_func)
    if nr_proc is None:
        nr_proc = multiprocessing.cpu_count()
    if nr_precompute is None:
        nr_precompute = nr_proc * 2

    pool = multiprocessing.Pool(nr_proc)
    results = deque()
    for i in iterator:
        results.append(pool.apply_async(map_func, [i]))
        if len(results) == nr_precompute:
            yield results.popleft().get()
    for r in results:
        yield r.get()
    pool.close()
    pool.join()
    pool.terminate()

def pmap(map_func, iterator, nr_proc=None, nr_precompute=None):
    '''parallel map'''
    return list(pimap(map_func, iterator, nr_proc, nr_precompute))
