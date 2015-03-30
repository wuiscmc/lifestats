"""

@author: Carlos Mateos

======================================
:mod: `main`
======================================
.. module:: main
    :synopsis: Provides the App 
"""

from collections import Counter
from multiprocessing import JoinableQueue, Lock
from multiprocessing.managers import SyncManager
import signal
from datetime import datetime
from .worker import WorkerPool
from .config import environment

class App(object):
    """
    ======================
    :class: `App`
    ======================
    .. module:: main
        :synopsis: Initializes the process of fetching the statistics 
        from the Lifesum API and displays them once the task is done.
        The App class maintains two Counters, food and categories, which are 
        updated upon `Worker` finish. This means that everytime a `Worker`
        is done processing its subset of entries, its data will be aggregated
        into the aforementioned Counters. When the `WorkerPool` runs out of 
        active `Worker` instances, this class will display the statistics.

        Upon interruption signal (SIGINT), the App shuts down the event loop,
        and displays the fetched statistics.

    .. author: Carlos Mateos
    """

    def __init__(self):
        self.manager = SyncManager()
        self.manager.start(self._register_handler_manager)
        self.foods = Counter()
        self.categories = Counter()
        self.queue = JoinableQueue()
        self.worker_pool = WorkerPool(self.queue)

    def start(self):
        try: 
            self.worker_pool.start()
            self.start_time = datetime.now()
            self._start_event_loop()
            self.worker_pool.shutdown()
        except KeyboardInterrupt: 
            data = self.queue.get()
            self._stats_aggregator(data)
            self.worker_pool.terminate_all()
        finally:
            display = Display(
                foods=self.foods.most_common(100), 
                categories=self.categories.most_common(10), 
                start_time=self.start_time, 
                end_time=datetime.now()
            )
            return display.print_statistics()

    def _start_event_loop(self):
        while True:
            data = self.queue.get()
            self._stats_aggregator(data)
            self.worker_pool.pop()
            self.queue.task_done()
            if not self.worker_pool.any_active(): break

    def _register_handler_manager(self):
        signal.signal(signal.SIGINT, signal.SIG_IGN)

    def _stats_aggregator(self, stats):
        self.foods.update(stats['food_ids'])
        self.categories.update(stats['categories'])



class Display(object):
    """
    ======================
    :class: `Display`
    ======================
    .. module:: main
        :synopsis: Displays the fetched information

    .. author: Carlos Mateos
    """
    def __init__(self, foods, categories, start_time, end_time):
        self.foods = foods
        self.categories = categories
        self.start_time = start_time
        self.end_time = end_time

    def print_statistics(self):
        return {
          'development': self._development,
          'production': self._production,
          'test': self._test
        }[environment]()

    def _print_list(self, name, collection):
        self._print("\nItem\t%s\r\t\t\tFrequency" % name)
        self._print("=================================")
        i = 1
        for (key, item) in collection: 
            self._print("%d\t%d\r\t\t\t%d" % (i, key, item))
            i += 1

    def _development(self):
        self._print("\n")
        self._print(self.foods)
        self._print(self.categories)

    def _production(self):
        self._print("\n=================================")
        self._print("\tRESULTS")
        self._print("=================================")
        self._print_list('Food id', self.foods)
        self._print_list('Categories', self.categories)

        self._print("\nStarted at %s" %  self.start_time.strftime("%H:%M:%S"))
        self._print("Finished at %s" % self.end_time.strftime("%H:%M:%S"))

    def _test(self):
        return {
            'foods': self.foods,
            'categories': self.categories
        }

    def _print(self, string=None):
        """ Just a wrapper so it is easy to define different strategies"""
        print string
