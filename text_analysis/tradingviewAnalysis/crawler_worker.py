from threading import Thread
from accounts import *
from utils import execute_sql, write_in_log
from crawlerFunctions import getAllPostsInMarket

class Worker(Thread):
  def __init__(self, lock, user):
    Thread.__init__(self)
    self.lock = lock
    self.user_name = user