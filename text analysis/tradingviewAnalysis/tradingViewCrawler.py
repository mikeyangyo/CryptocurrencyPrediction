#!/usr/bin/python
# coding:utf-8

import argparse
import time

from typeChecking import dateChecking
from crawlerFunctions import getAllPostsInMarket
from datetime import datetime
from utils import getUserListFromFile, execute_sql, write_in_log
from accounts import *

def main():
    parser = argparse.ArgumentParser(description='crawler for tradingview.com')

    # Optional argument
    parser.add_argument('-d',
                        '--date',
                        help='the require day, format should be yyyy-mm-dd',
                        type = dateChecking
                        )

    parser.add_argument('-n',
                        '--now',
                        help='update post data newer than newest data in database',
                        )

    parser.add_argument('-au',
                        '--alluser',
                        action='store_true',
                        dest='alluser',
                        help='crawl posts of all user provide by file',
                        )

    parser.set_defaults(alluser=False)

    args = vars(parser.parse_args())

    selectMarket = 'cryptocurrencies'

    start = time.time()
    print('start crawling...')
    if args['alluser']:
        user_list = getUserListFromFile()
        for user in user_list:
            # check existence of user
            sql = 'select user_name from {schema}.{table} where user_name = "{user_name}"'.format(schema = SCHEMA, table = table_name_set['user'], user_name = user)
            result, msgs, _ = execute_sql(db_info=db_info_tradingview, operation_name='select', sql=sql)
            write_in_log(file_location=LOG_FILE, msgs=msgs)
            if not result:
                sql = 'insert into {schema}.{table}(user_name, accuracy_so_far) values ("{user_name}", 0)'.format(schema = SCHEMA, table = table_name_set['user'], user_name = user)
                result, msgs, _ = execute_sql(db_info=db_info_tradingview, operation_name='insert', sql=sql)
                write_in_log(file_location=LOG_FILE, msgs=msgs)

            targetURL = 'https://www.tradingview.com/u/{}/'.format(user)

            write_in_log(file_location=LOG_FILE, msgs=['start crawling {}\'s posts'.format(targetURL)], )
            getAllPostsInMarket(targetURL, crawl_status = 'alluser')
            write_in_log(file_location=LOG_FILE, msgs=['finish crawling {}\'s posts'.format(targetURL)], )
    elif args['date'] is None and args['now'] is None:
        # get all post at specific market
        print('get all post at specific market...')
        targetURL = 'https://www.tradingview.com/markets/{0}/ideas/'.format(selectMarket)
        getAllPostsInMarket(targetURL, crawl_status = 'allpost')
    elif args['date'] is not None and args['now'] is None:
        # get post on specific date at specific market
        selectDate = args['date']
        targetURL = 'https://www.tradingview.com/markets/{0}/ideas/'.format(selectMarket)
        getAllPostsInMarket(targetURL, selectDate, crawl_status = 'allpost')
    else:
        # check the post date of newest post in database
        # crawl all post after the date
        pass
    print('finish crawling...')

if __name__ == '__main__':
    main()