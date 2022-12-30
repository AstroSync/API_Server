from __future__ import annotations
from threading import Thread
# from typing import Any, Callable, Iterable, Mapping
import time

# class ThreadWithReturnValue(Thread):
#     def __init__(self, group=None, target=None, name=None,
#                  args=(), kwargs=None, daemon=None, time_limit=None) -> None:
#         super().__init__(group, target, name, args, kwargs, daemon=daemon)
#         self._return = None
#         self._args = args
#         self._target = target
#         self._kwargs = kwargs
#         self._time_limit = time_limit
#         self._limit_counter = 0
#         if self._time_limit is not None:
#             self.limit_thread = Thread(name=f'{self.name} timer', target=self._time_limit_watcher, daemon=True)

#     def _time_limit_watcher(self):
#         if self._time_limit is not None:
#             while True:
#                 if self._limit_counter >= self._time_limit:
#                     print(f'{self.name} thread stop')
#                     self.stop()
#                 time.sleep(0.1)
#                 self._limit_counter += 0.1

#     def run(self):
#         if self._target is not None:
#             if self._time_limit is not None:
#                 self.limit_thread.start()
#                 #self.limit_thread.join()

#             self._return = self._target(*self._args, **self._kwargs if self._kwargs is not None else {})
#             print("end")
#     def join(self, *args):
#         Thread.join(self, *args)
#         return self._return

#     def stop(self):
#         raise RuntimeError(f'Stop event in {self.name} thread')
from func_timeout import func_timeout, FunctionTimedOut, func_set_timeout

@func_set_timeout(3)
def target_func(arg: int):
    for i in range(arg):
        print(f'{i=}')
        time.sleep(1)
    return 'Success'

# try:
#     doitReturnValue = func_timeout(3, target_func, args=([5]))
# except FunctionTimedOut as err:
#     print(err)
#     print ( "doit('arg1', 'arg2') could not complete within 5 seconds and was terminated.\n")

# target_func(6)




if __name__ == '__main__':
    # thread1 = ThreadWithReturnValue(name='th1', target=target_func, daemon=True, args=[5], time_limit=2)
    # thread2 = ThreadWithReturnValue(name='th2', target=target_func, daemon=True, args=[8])
    # thread1.start()
    # thread2.start()
    # thread1 = Thread(name='th1', target=func_timeout, args=[3, target_func, [5]])
    thread2 = Thread(name='th2', target=target_func, args=[8])
    # thread1.start()
    thread2.start()
    time.sleep(8)
    # try:
    #     thread1.stop()
    # except RuntimeError as err:
    #     print(err)

    # target_func(5)
