"""

@author: Carlos Mateos

======================================
:mod: `worker`
======================================
.. module:: worker
    :synopsis: Provides a process pool helper class and worker class to query the Lifesums API
"""
from __future__ import division
from collections import Counter
from multiprocessing import Process
from datetime import datetime
from .config import config
import time
import requests
import sys


class WorkerPool(object):
    """
    ======================
    :class: `WorkerPool`
    ======================
    .. module:: `worker`
    :synopsis: The `WorkerPool` manages a collection of `Worker`. 
        It is in charge of starting and shutting down the workers 
        and knows how many are active.

    .. author: Carlos Mateos
    
    :param queue: The shared Queue to include the results
    """ 

    def __init__(self, queue, pool_size=config['pool']):
        self.active_workers = pool_size
        self.workers = []
        self.queue = queue

    def pop(self):
        self.active_workers -= 1

    def any_active(self):
        return self.active_workers > 0

    def shutdown(self):
        for worker in self.workers: 
            worker.join()

    def terminate_all(self):
        for worker in self.workers: 
            worker.terminate()

    def start(self, session=requests.Session()):
        for i in xrange(self.active_workers):
            worker = Worker(
                worker_id=i,
                begin=self._min_limit(i), 
                end=self._max_limit(i), 
                queue=self.queue,
                session=session
            )
            worker.start()
            self.workers.append(worker)

    def _pool_offset_space(self):
        return int((config['last_id'] - config['first_id']) / config['pool'])

    def _min_limit(self, worker_index):
        return config['first_id'] + (self._pool_offset_space() * worker_index)

    def _max_limit(self, worker_index):
        max_id = config['first_id'] + (self._pool_offset_space() * (worker_index + 1))
        return max_id if worker_index < config['pool'] - 1 else config['last_id']


class Worker(Process): 
    """
        ======================
        :class: `Worker`
        ======================
        .. module:: `worker`
        :synopsis: The `Worker` requests the data to the API and stores the frequencies in temporary Counters.
            When it has fetched the remote data, it sends its the extracted data back to the Main process.
            It logs every `log_span` seconds the progress to the console.

        .. author: Carlos Mateos
        
        :param worker_id: an unique identifier (just for displaying purposes)
        :param begin: The starting offset for this Worker 
        :param end: The last item id 
        :param queue: The shared Queue to include the results
        :param session: Shared session among the workers
    """ 


    def __init__(self, worker_id, begin, end, queue, session):
        self.worker_id = worker_id
        self.begin = begin
        self.end = end
        self.rate_limiter = RateLimiter()
        self.queue = queue
        self.session = session
        self.foods = Counter()
        self.categories = Counter()
        self.logger = Log(worker_id, datetime.now(), begin, end)
        super(Worker, self).__init__()

    def run(self):
        try:    
            self._start_event_loop()
        except KeyboardInterrupt:
            pass
        finally: 
            self._send_frequencies()

    def _start_event_loop(self):
        next_offset = self.begin
        self.rate_limiter.start()
        while next_offset < self.end and next_offset is not None:
            self.rate_limiter.limit()
            data = self._fetch_data(next_offset)
            self._update_counters(data['response'])
            self.logger.log(next_offset, self.rate_limiter.reqs_second)
            next_offset = data['meta']['next_offset']

    def _fetch_data(self, offset):
        response = self.session.get(url=config['url'], params={'offset': offset, 'limit': config['results_per_page']})
        if response.status_code != requests.codes.ok:
            raise RuntimeError('Request failed: Could not fetch data for offset %d from API' % offset)
        return response.json()

    def _send_frequencies(self):
        self.queue.put({ 
            'food_ids': self.foods, 
            'categories': self.categories
        })

    def _update_counters(self, items):
        for item in items: 
            if item['id'] < self.end:
                self.foods[item['food_id']] += 1
                self.categories[item['food__category_id']] += 1


class Log(object):
    """
        ======================
        :class: `Log`
        ======================
        .. module:: `worker`
        :synopsis: It prints the progress of a worker to stdout

        .. author: Carlos Mateos
    """ 
    def __init__(self, worker_id, start_time, begin, end):
        self.worker_id = worker_id
        self.min_limit = begin
        self.last_log_time = start_time
        self.total_pages = self._page_distance(end, begin)
        self.log_span = int(config['log_span'])

    def log(self, offset, stats=None):
        delta = (datetime.now() - self.last_log_time).seconds
        if delta == self.log_span:
            self.last_log_time = datetime.now()
            progress = self._calculate_progress(offset)
            sys.stdout.write("\rworker %d: %d%% - %f req/sec" % (self.worker_id, progress, stats))
        if delta < self.log_span:
            sys.stdout.flush()

    def _calculate_progress(self, offset):
        return int((self._page_distance(offset, self.min_limit) * 100) / self.total_pages)

    def _page_distance(self, max_limit, min_limit):
        return int((max_limit - self.min_limit) / config['results_per_page'])



class RateLimiter(object):
    """
        ======================
        :class: `RateLimiter`
        ======================
        .. module:: `worker`
        :synopsis: It implements a strategy of rate limiting and helper to extract statistics of the requests sent to the server
            The strategy followed assigns a portion of the rate limit to every process. In case we have a pool of 2 processes and
            a rate limit of 2 req/second then each process can only perform 1 req/sec.

            Original seen here: <http://stackoverflow.com/a/667706>

        .. authors: Carlos A. Ibarra, Carlos Mateos
    """ 
    def __init__(self, rate_limit=config['rate_limit'], pool_size=config['pool']):
        self.rate_limit = rate_limit / pool_size
        self.last_request = None
        self.requests = []

    def start(self):
        self.last_request = time.time()

    def limit(self):
        elapsed = time.time() - self.last_request
        wait_time = (1.0 / self.rate_limit) - elapsed
        if wait_time > 0: time.sleep(wait_time)
        self._register_request(wait_time)
        self.last_request = time.time()

    @property
    def reqs_second(self):
        return sum(self.requests) / len(self.requests)

    def _register_request(self, elapsed):
        self.requests.append(elapsed)
