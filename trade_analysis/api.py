from requests import request
from requests.compat import urljoin
from functools import reduce
from json import loads
from datetime import datetime, timedelta
from funcy.flow import retry
from time import sleep, time
from re import search

from accounts import db_info_trades, SCHEMA, TABLE_NAME_BASE, LOG_FILE_PATH
from utils import execute_sql, write_in_log

def ms2s(secs):
    return secs / 1000.0

@retry(tries=3, timeout=3)
def get_bitfinex_data(endpoint, currency_type, version = 'v2', **kwargs):
    if endpoint == 'trades':
        col_name2index = [
            'id',
            'trade_time',
            'amount',
            'price'
        ]
        endpoint_url = 'https://api.bitfinex.com/{}/{}/{}/hist'.format(version, endpoint, currency_type)
        params = {
            'limit' : kwargs['limit'] if 'limit' in kwargs.keys() else None,
            'start' : kwargs['start'] if 'start' in kwargs.keys() else None,
            'end' : kwargs['end'] if 'end' in kwargs.keys() else None,
            'sort' : kwargs['sort'] if 'sort' in kwargs.keys() else None
        }
        response = request("GET", endpoint_url, params = params)
        response.raise_for_status()
        response = loads(response.text)
        response = [{col_name:record[col_name2index.index(col_name)] if col_name != 'trade_time' else datetime.fromtimestamp(ms2s(record[col_name2index.index(col_name)])) for col_name in col_name2index} for record in response]
        return response

if __name__ == '__main__':
    endpoint = 'trades'
    currency_type = 'tBTCUSD'
    
    print('process start')
    write_in_log(LOG_FILE_PATH, ['[{}] process start\n'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))])
    need_to_get_data = True
    sql = 'show tables from {}'.format(SCHEMA)
    result, msg = execute_sql(db_info_trades, 'select', sql)
    write_in_log(LOG_FILE_PATH, msg)
    last_table_name = [row['Tables_in_{}'.format(SCHEMA)] for row in result][-1]
    matches = search("trades_data_(.*)", last_table_name)
    start_date = "2018_01_01"
    if matches:
        start_date = matches.group(1)
    table_name=TABLE_NAME_BASE+start_date
    sql = 'select trade_time from {schema}.{table} order by trade_time desc'.format(schema=SCHEMA, table=table_name)
    result, msg = execute_sql(db_info_trades, 'select', sql)
    write_in_log(LOG_FILE_PATH, msg)
    if result[0]['trade_time'] < datetime.now():
        start_timestamp_ms = int(result[0]['trade_time'].timestamp() * 1000)
        need_to_get_data = True
    else:
        need_to_get_data = False
    end_timestamp_ms = int(datetime.now().timestamp() * 1000)

    while need_to_get_data:
        # try:
            api_result = get_bitfinex_data(endpoint, currency_type, limit = 1000, start=start_timestamp_ms, end=end_timestamp_ms, sort=1)
            # start_process_time = time()
            last_date_of_record = api_result[-1]['trade_time']
            if last_date_of_record >= datetime.now():
                need_to_get_data = False
            else:
                start_time = last_date_of_record + timedelta(seconds=1)
                start_timestamp_ms = int(start_time.timestamp() * 1000)
                # check if table exist
                sql = 'show tables from {}'.format(SCHEMA)
                result, msg = execute_sql(db_info_trades, 'select', sql)
                write_in_log(LOG_FILE_PATH, msg)
                last_table_name = [row['Tables_in_{}'.format(SCHEMA)] for row in result][-1]
                matches = search("trades_data_(.*)", last_table_name)
                last_date_in_db = matches.group(1)
                if datetime.strptime(last_date_in_db, "%Y_%m_%d").date() < start_time.date():
                    # create table
                    table_name = TABLE_NAME_BASE + start_time.strftime("%Y_%m_%d")
                    sql = 'CREATE TABLE {new_schema}.{new_table} LIKE {new_schema}.{old_table}'.format(
                        new_schema = SCHEMA,
                        new_table = table_name,
                        old_table = 'trades_data_2018_01_01'
                    )
                    result, msg = execute_sql(db_info_trades, 'insert', sql)
                    write_in_log(LOG_FILE_PATH, msg)
                
            insert_sql = 'Insert into {schema}.{table}(tid, trade_price, trade_amount, trade_time, status) values '.format(
                schema=SCHEMA,
                table=table_name
            )
            value_list = []
            for record in api_result:
                # check if table exist
                trade_time = record['trade_time']
                sql = 'show tables from {}'.format(SCHEMA)
                result, msg = execute_sql(db_info_trades, 'select', sql)
                write_in_log(LOG_FILE_PATH, msg)
                last_table_name = [row['Tables_in_{}'.format(SCHEMA)] for row in result][-1]
                matches = search("trades_data_(.*)", last_table_name)
                last_date_in_db = matches.group(1)
                if datetime.strptime(last_date_in_db, "%Y_%m_%d").date() < trade_time.date():
                    # create table
                    table_name = TABLE_NAME_BASE + trade_time.strftime("%Y_%m_%d")
                    sql = 'CREATE TABLE {new_schema}.{new_table} LIKE {new_schema}.{old_table}'.format(
                        new_schema = SCHEMA,
                        new_table = table_name,
                        old_table = 'trades_data_2018_01_01'
                    )
                    result, msg = execute_sql(db_info_trades, 'insert', sql)
                    write_in_log(LOG_FILE_PATH, msg)

                sql = 'select * from {schema}.{table} where tid = {id}'.format(
                    schema=SCHEMA,
                    table=table_name,
                    id=record['id']
                )
                query_result, msg = execute_sql(db_info_trades, 'select', sql)
                write_in_log(LOG_FILE_PATH, msg)
                if query_result:
                    record['status'] = 1 if record['amount'] > 0 else -1
                    if record != query_result:
                        sql = 'update {}.{} set trade_price = {}, trade_amount = {}, trade_time = {}, status = {} where tid = {}'.format(
                            SCHEMA,
                            table_name,
                            record['price'],
                            record['amount'],
                            record['trade_time'].strftime("%Y%m%d%H%M%S"),
                            record['status'],
                            record['id']
                        )
                        execute_sql(db_info_trades, 'update', sql)
                    continue
                value_list.append('({tid}, {trade_price}, {trade_amount}, "{trade_time}", {status})'.format(
                    tid=record['id'],
                    trade_price=record['price'],
                    trade_amount=record['amount'],
                    trade_time=record['trade_time'].strftime("%Y%m%d%H%M%S"),
                    status=1 if record['amount'] > 0 else -1
                ))
            insert_sql += ','.join(value_list)
            # print(sql)
            _, msg = execute_sql(db_info_trades, 'insert', insert_sql)
            write_in_log(LOG_FILE_PATH, msg)
            print('{} is crawled'.format(last_date_of_record.strftime('%Y-%m-%d %H:%M:%S')))
            # end_process_time = time()
            # process_time = start_process_time - end_process_time
            # sleep(6 - process_time)
        # except Exception as e:
        #     print(e)
        
    print('process finish')
    write_in_log(LOG_FILE_PATH, ['[{}] process finish\n'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))])