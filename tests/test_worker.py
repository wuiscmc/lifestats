import os
import time
from mock import MagicMock, Mock, patch
from nose.tools import *
from lifestats import worker
from collections import Counter
from lifestats.config import config
from multiprocessing import active_children, Queue
import requests
import responses

def mock_api_requests():
    responses.add(
        responses.GET, config['url'],
        body=_test_data(), 
        content_type='application/json')

@responses.activate
@with_setup(mock_api_requests)
def test_pool_control_child_processes_life():
    pool_size = 2
    pool = worker.WorkerPool(Queue(), pool_size)
    pool.start()
    assert_equal(len(pool.workers), pool_size)
    assert_equal(len(active_children()), pool_size)
    pool.shutdown()
    assert_equal(len(active_children()), 0)

@responses.activate
@with_setup(mock_api_requests)
def test_pool_uses_same_session():
    pool = worker.WorkerPool(Queue(), 2)
    pool.start()
    assert_equals(pool.workers[0].session, pool.workers[1].session)
    pool.shutdown()

@responses.activate
@with_setup(mock_api_requests)
def test_pool_splits_item_space():
    config['pool'] = 4
    pool = worker.WorkerPool(Queue(), config['pool'])
    pool.start()
    assert_equal(pool.workers[0].begin, config['first_id'])
    assert_equal(pool.workers[0].end, pool.workers[1].begin)
    assert_equal(pool.workers[1].end, pool.workers[2].begin)
    assert_equal(pool.workers[2].end, pool.workers[3].begin)
    assert_equal(pool.workers[3].end, config['last_id'])
    pool.shutdown()

@responses.activate
def test_worker_puts_data_in_queue_when_finishes():
    responses.add(responses.GET, config['url'], body=_test_data("test.json"), content_type='application/json')
    queue = Queue()
    proc = worker.Worker(
        worker_id=0,
        begin=config['first_id'],
        end=config['last_id'], 
        queue=queue,
        session=requests.Session()
    )
    proc.start()
    proc.join()
    data = queue.get()
    
    assert_equal(data['food_ids'], Counter({1:2,2:1,3:1}))
    assert_equal(data['categories'], Counter({1:3,2:1}))


@responses.activate
@with_setup(mock_api_requests)
def test_worker_fetches_data_from_api():
    proc = _test_worker()
    proc.run()
    assert len(responses.calls) == 1
    url = config['url'] + "?limit=" + str(config['results_per_page']) + "&offset=" + str(config['first_id'])
    assert_equal(responses.calls[0].request.url, url)


@responses.activate
@with_setup(mock_api_requests)
def test_worker_rate_is_limited():
    proc = _test_worker()
    time.sleep = MagicMock()
    proc.run()
    assert_true(time.sleep.called)
    

def _test_worker():
    return worker.Worker(
        worker_id=0,
        begin=config['first_id'],
        end=config['last_id'], 
        queue=MagicMock(),
        session=requests.Session()
    )

def _test_data(file="20.json"):
    """ Finds the abs path of the test data file so the 
    tests run from everywhere"""
    main_base = os.path.dirname(__file__)
    path = os.path.join(main_base, "..", "mocks",file)
    return open(path).read()


