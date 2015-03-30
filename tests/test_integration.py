import time
import os
from nose.tools import *
import subprocess
import signal
from multiprocessing import active_children
from main import App

def test_system_retrieves_the_statistics_from_api():
    """
        Tests the integration against a test API server. 
        Rate limit = 10 request/second
        Pool size = 2 
        See config.yml
    """

    try:
        server = create_server()
        data = App().start()
        assert_equal(len(data['foods']), 100)
        assert_equal(len(data['categories']), 10)
    finally:
        stop_server(server)

def create_server():
    main_base = os.path.dirname(__file__)
    path = os.path.join(main_base, "..", "mocks", "api.rb")
    proc = subprocess.Popen(['ruby', path], shell=False)
    time.sleep(3)
    return proc

def stop_server(server):
    os.kill(server.pid, signal.SIGTERM)