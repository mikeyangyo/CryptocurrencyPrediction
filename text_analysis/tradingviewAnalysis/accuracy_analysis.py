from accounts import db_info_tradingview, table_name_set, SCHEMA, ANALYSIS_LOG_FILE, db_info_price_data, PRICE_SCHEMA, PRICE_TABLES
from utils import execute_sql, write_in_log, getUserListFromFile
from crawler_worker import Worker

from datetime import timedelta, datetime
from funcy.seqs import pairwise
from numpy import diff
from threading import Lock
from pandas import DataFrame

class AccuracyAnalysisWorker(Worker):
    def __init__(self, lock, user):
        super(AccuracyAnalysisWorker, self).__init__(lock, user)

    def run(self):
        accuracy_determined(self.user_name, lock=self.lock)
        accuracy_analysis(self.user_name, lock=self.lock)


def get_trend(start_time, end_time, crypto_type, **kwargs):
    assert isinstance(start_time, datetime), "type of start_time is not datetime"
    assert isinstance(end_time, datetime), "type of end_time is not datetime"
    assert crypto_type in PRICE_TABLES.keys(), "{} is not in price table keys".format(crypto_type)
    assert 'lock' in kwargs.keys(), "lock is not in kwargs keys"
    sql = 'select CLOSE from {}.{} where DATE between "{}" and "{}" order by DATE'.format(
        PRICE_SCHEMA,
        PRICE_TABLES[crypto_type],
        (start_time - timedelta(days=1)).strftime("%Y-%m-%d"),
        (end_time + timedelta(days=1)).strftime("%Y-%m-%d")
    )
    result, msg = execute_sql(db_info_price_data, 'select', sql, lock=kwargs['lock'])
    write_in_log(ANALYSIS_LOG_FILE, msg, lock=kwargs['lock'])

    assert result, "no price data from {} to {}".format((start_time - timedelta(days=1)).strftime("%Y-%m-%d"),
        (end_time + timedelta(days=1)).strftime("%Y-%m-%d"))
    close_price_list = [i['CLOSE'] for i in result]
    print(close_price_list)
    print(diff(close_price_list))
    return [1 if i > 0 else 0 if i == 0 else -1 for i in diff(close_price_list)]


def accuracy_determined(user_name, crypto_type='btc', **kwargs):
    assert 'lock' in kwargs.keys(), 'there are no lock in kwargs'
    assert 'user' in table_name_set.keys(), 'user is not in table_name_set keys'
    assert 'accuracy' in table_name_set.keys(), 'accuracy is not in table_name_set keys'

    sql = 'select id from {}.{} where user_name = "{}"'.format(
        SCHEMA,
        table_name_set['user'],
        user_name
    )
    user_result, msg = execute_sql(db_info_tradingview, 'select', sql, lock=kwargs['lock'])
    write_in_log(ANALYSIS_LOG_FILE, msg, lock=kwargs['lock'])
    assert user_result, "result is empty"
    user_id = user_result[0]['id']
    sql = 'select * from {}.{} where user_id = {} order by last_analysis_date desc limit 1'.format(
        SCHEMA, table_name_set['accuracy'],
        user_id
    )
    result, msg = execute_sql(
        db_info_tradingview, 'select', sql, lock=kwargs['lock'])
    write_in_log(ANALYSIS_LOG_FILE, msg, lock=kwargs['lock'])
    if result:
        sql = 'select * from {}.{} where author = {} and created_time > {} order by created_time'.format(
            SCHEMA, table_name_set['idea'],
            user_id,
            result[0]["last_analysis_date"].strftime("%Y%m%d%H%M%S"))
        ideas, msg = execute_sql(
            db_info_tradingview, 'select', sql, lock=kwargs['lock'])
        write_in_log(ANALYSIS_LOG_FILE, msg, lock=kwargs['lock'])
    else:
        sql = 'select * from {}.{} where author = {} and crypto_type = "{}" order by created_time'.format(
            SCHEMA, table_name_set['idea'],
            user_id,
            crypto_type
        )
        ideas, msg = execute_sql(
            db_info_tradingview, 'select', sql, lock=kwargs['lock'])
        write_in_log(ANALYSIS_LOG_FILE, msg, lock=kwargs['lock'])
    for idea in pairwise(ideas):
        assert len(idea) == 2, "len of idea didn't equal to 2"
        start_time = idea[0]['created_time'] + timedelta(days=1)
        end_time = idea[1]['created_time']
        if start_time > end_time:
            continue
        predict_trend = 1 if idea[0]['label'].lower() == 'long' else -1 if idea[0]['label'].lower() == 'short' else 0
        assert predict_trend != 0, "label of the idea is neither 'long' nor 'short'"
        trend_list = get_trend(start_time, end_time, crypto_type + '_usd', **kwargs)
        print(trend_list)
        print(predict_trend)
        print(trend_list.count(predict_trend))
        print(len(trend_list))
        accuracy = trend_list.count(predict_trend) / len(trend_list)
        sql = 'select id from {}.{} where user_id={} and crypto_type="{}" and accuracy={} and last_analysis_date="{}"'.format(
            SCHEMA,
            table_name_set['accuracy'],
            user_id,
            crypto_type,
            accuracy,
            end_time.strftime("%Y%m%d%H%M%S")
        )
        result, msg = execute_sql(db_info_tradingview, 'select', sql, lock=kwargs['lock'])
        write_in_log(ANALYSIS_LOG_FILE, msg, lock=kwargs['lock'])
        if not result:
            sql = 'insert into {}.{}(user_id, crypto_type, accuracy, last_analysis_date) values ({},"{}",{},"{}")'.format(
                SCHEMA, 
                table_name_set['accuracy'],
                user_id,
                crypto_type,
                accuracy,
                end_time.strftime("%Y%m%d%H%M%S")
            )
            _, msg = execute_sql(db_info_tradingview, 'insert', sql, lock=kwargs['lock'])
            write_in_log(ANALYSIS_LOG_FILE, msg, lock=kwargs['lock'])

def accuracy_analysis(username, crypto_type='btc', **kwargs):
    assert 'lock' in kwargs.keys(), 'lock is not in kwargs keys'
    sql = 'select accuracy, user_id from {schema}.{accuracy_table} t1 join {schema}.{user_table} t2 where t1.user_id=t2.id and t2.user_name="{user_name}"'.format(
        schema=SCHEMA,
        accuracy_table=table_name_set['accuracy'],
        user_table=table_name_set['user'],
        user_name=username
    )
    accuracy_result, msg=execute_sql(db_info_tradingview, 'select', sql, lock=kwargs['lock'])
    write_in_log(ANALYSIS_LOG_FILE, msg, lock=kwargs['lock'])
    if accuracy_result:
        accuracy_df = DataFrame(accuracy_result)
        ema_accuracy = accuracy_df.ewm(span=len(accuracy_df.index), adjust=False).mean()
        accuracy_of_prediction = list(ema_accuracy['accuracy'])[-1]
    else:
        accuracy_of_prediction = 0

    sql = 'update {}.{} set accuracy_so_far = {} where id={}'.format(
        SCHEMA,
        table_name_set['user'],
        accuracy_of_prediction,
        accuracy_result[0]['user_id']
    )
    _, msg=execute_sql(db_info_tradingview, 'update', sql, lock=kwargs['lock'])
    write_in_log(ANALYSIS_LOG_FILE, msg)

if __name__ == '__main__':
    user_list = getUserListFromFile()
    threads = []
    lock = Lock()
    for name in user_list:
        threads.append(AccuracyAnalysisWorker(lock, name))
    
    for i in range(len(user_list)):
        threads[i].start()

    for i in range(len(user_list)):
        threads[i].join()