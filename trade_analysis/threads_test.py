from threading import Thread, Lock
from utils import execute_sql
from accounts import db_info_trades, SCHEMA

def job(table_name):
    sql = 'select * from {}.{} where trade_amount < 0'.format(SCHEMA, table_name)
    result, msg = execute_sql(db_info_trades, 'select', sql)
    print(msg)
    print(result)

class Worker(Thread):
  def __init__(self, job_func, lock, table_name):
    Thread.__init__(self)
    self.job_func = job_func
    self.lock = lock
    self.target = table_name

  def run(self):
      self.lock.acquire()
      print('get lock')
      self.job_func(self.target)
      self.lock.release()
      print('release lock')


sql = 'show tables from {}'.format(SCHEMA)
result, msg = execute_sql(db_info_trades, 'select', sql)
print(result)
table_names = [value for instance in result for i, value in instance.items()]
threads = []
lock = Lock()
for name in table_names[:10:-1]:
    threads.append(Worker(job, lock, name))

for i in range(10):
    threads[i].start()

for i in range(10):
    threads[i].join()

print('Done')