# Copyright (c) 2010 Resolver Systems Ltd, PythonAnywhere LLP
# See LICENSE.md
#
from ctypes import c_long, py_object, pythonapi
from threading import _active, Thread

class TimeoutException(Exception):
    pass

class InterruptableThread(Thread):

    def _get_thread_id(self):
        if hasattr(self, "_thread_id"):
            return self._thread_id
        for tid, tobj in _active.items():
            if tobj is self:
                self._thread_id = tid
                return tid


    def interrupt(self):
        if not self.isAlive():
            return
        tid = self._get_thread_id()
        threads_affected = pythonapi.PyThreadState_SetAsyncExc(c_long(tid), py_object(TimeoutException))
        if threads_affected != 1:
            # if it returns a number greater than one, you're in trouble,
            # and you should call it again with exc=NULL to revert the effect
            pythonapi.PyThreadState_SetAsyncExc(c_long(tid), None)
            raise SystemError("PyThreadState_SetAsyncExc failed")
