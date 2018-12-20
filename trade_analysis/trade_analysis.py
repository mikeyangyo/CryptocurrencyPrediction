from accounts import SCHEMA, FEATURES_SCHEMA, FEATURES_TABLE, db_info_features, ANALYSIS_LOG_FILE_PATH, TRADES_DATA_ANALYSIS_FEATURES
from utils import execute_sql, write_in_log
from re import search
from datetime import datetime
import numpy as np

if __name__ == '__main__':
    sql = 'show tables from {}'.format(SCHEMA)
    table_result, msg = execute_sql(db_info_features, 'select', sql)
    write_in_log(ANALYSIS_LOG_FILE_PATH, msg)
    for i in table_result:
        table_name = i['Tables_in_{}'.format(SCHEMA)]
        matches = search('trades_data_(.*)', table_name)
        if matches:
            value_dict = {}
            trades_date = matches.group(1)
            now_date = datetime.strptime(trades_date, '%Y_%m_%d')
            value_dict['trade_time'] = now_date.strftime('%Y%m%d%H%M%S')
            sql = 'select *, trade_price * trade_amount as "trade_cost" from {}.{} order by trade_time'.format(SCHEMA, table_name)
            result, msg = execute_sql(db_info_features, 'select', sql)
            write_in_log(ANALYSIS_LOG_FILE_PATH, msg)
            print('start to analyse trades data of {}'.format(trades_date))
            cost_list = [value for row in result for key, value in row.items() if key == 'trade_cost']
            cost_list_long = [row for row in result if row['status'] == 1]
            cost_list_short = [row for row in result if row['status'] == -1]

            cost_list_len = len(cost_list)
            cost_list_long_len = len(cost_list_long)
            cost_list_short_len = len(cost_list_short)

            long_ratio_of_cost_list = cost_list_long_len / cost_list_len
            short_ratio_of_cost_list = cost_list_short_len / cost_list_len
            value_dict['long_ratio_of_cost_list'] = long_ratio_of_cost_list
            value_dict['short_ratio_of_cost_list'] = short_ratio_of_cost_list

            cost_25_percentile = np.percentile(cost_list, 25)
            cost_50_percentile = np.percentile(cost_list, 50)
            cost_75_percentile = np.percentile(cost_list, 75)

            cost_0to25_percentile_list = [row for row in result if row['trade_cost'] <= cost_25_percentile]
            cost_26to50_percentile_list = [row for row in result if row['trade_cost'] > cost_25_percentile and row['trade_cost'] <= cost_50_percentile]
            cost_51to75_percentile_list = [row for row in result if row['trade_cost'] > cost_50_percentile and row['trade_cost'] <= cost_75_percentile]
            cost_76to100_percentile_list = [row for row in result if row['trade_cost'] > cost_75_percentile]

            cost_0to25_percentile_list_len = len(cost_0to25_percentile_list)
            cost_26to50_percentile_list_len = len(cost_26to50_percentile_list)
            cost_51to75_percentile_list_len = len(cost_51to75_percentile_list)
            cost_76to100_percentile_list_len = len(cost_76to100_percentile_list)

            cost_0to25_percentile_list_long = [row for row in cost_0to25_percentile_list if row['status'] == 1]
            cost_26to50_percentile_list_long = [row for row in cost_26to50_percentile_list if row['status'] == 1]
            cost_51to75_percentile_list_long = [row for row in cost_51to75_percentile_list if row['status'] == 1]
            cost_76to100_percentile_list_long = [row for row in cost_76to100_percentile_list if row['status'] == 1]

            cost_0to25_percentile_list_short = [row for row in cost_0to25_percentile_list if row['status'] == -1]
            cost_26to50_percentile_list_short = [row for row in cost_26to50_percentile_list if row['status'] == -1]
            cost_51to75_percentile_list_short = [row for row in cost_51to75_percentile_list if row['status'] == -1]
            cost_76to100_percentile_list_short = [row for row in cost_76to100_percentile_list if row['status'] == -1]

            long_ratio_of_cost_0to25_percentile_list = len(cost_0to25_percentile_list_long) / cost_0to25_percentile_list_len if cost_0to25_percentile_list_len != 0 else 0
            long_ratio_of_cost_26to50_percentile_list = len(cost_26to50_percentile_list_long) / cost_26to50_percentile_list_len if cost_26to50_percentile_list_len != 0 else 0
            long_ratio_of_cost_51to75_percentile_list = len(cost_51to75_percentile_list_long) / cost_51to75_percentile_list_len if cost_51to75_percentile_list_len != 0 else 0
            long_ratio_of_cost_76to100_percentile_list = len(cost_76to100_percentile_list_long) / cost_76to100_percentile_list_len if cost_76to100_percentile_list_len != 0 else 0

            value_dict['long_ratio_of_cost_0to25_percentile_list'] = long_ratio_of_cost_0to25_percentile_list
            value_dict['long_ratio_of_cost_26to50_percentile_list'] = long_ratio_of_cost_26to50_percentile_list
            value_dict['long_ratio_of_cost_51to75_percentile_list'] = long_ratio_of_cost_51to75_percentile_list
            value_dict['long_ratio_of_cost_76to100_percentile_list'] = long_ratio_of_cost_76to100_percentile_list

            long_ratio_of_cost_0to25_percentile_over_all_records = len(cost_0to25_percentile_list_long) / cost_list_len if cost_list_len != 0 else 0
            long_ratio_of_cost_26to50_percentile_over_all_records = len(cost_26to50_percentile_list_long) / cost_list_len if cost_list_len != 0 else 0
            long_ratio_of_cost_51to75_percentile_over_all_records = len(cost_51to75_percentile_list_long) / cost_list_len if cost_list_len != 0 else 0
            long_ratio_of_cost_76to100_percentile_over_all_records = len(cost_76to100_percentile_list_long) / cost_list_len if cost_list_len != 0 else 0

            value_dict['long_ratio_of_cost_0to25_percentile_over_all_records'] = long_ratio_of_cost_0to25_percentile_over_all_records
            value_dict['long_ratio_of_cost_26to50_percentile_over_all_records'] = long_ratio_of_cost_26to50_percentile_over_all_records
            value_dict['long_ratio_of_cost_51to75_percentile_over_all_records'] = long_ratio_of_cost_51to75_percentile_over_all_records
            value_dict['long_ratio_of_cost_76to100_percentile_over_all_records'] = long_ratio_of_cost_76to100_percentile_over_all_records

            long_ratio_of_cost_0to25_percentile_over_long = len(cost_0to25_percentile_list_long) / cost_list_long_len if cost_list_len != 0 else 0
            long_ratio_of_cost_26to50_percentile_over_long = len(cost_26to50_percentile_list_long) / cost_list_long_len if cost_list_len != 0 else 0
            long_ratio_of_cost_51to75_percentile_over_long = len(cost_51to75_percentile_list_long) / cost_list_long_len if cost_list_len != 0 else 0
            long_ratio_of_cost_76to100_percentile_over_long = len(cost_76to100_percentile_list_long) / cost_list_long_len if cost_list_len != 0 else 0

            value_dict['long_ratio_of_cost_0to25_percentile_over_long'] = long_ratio_of_cost_0to25_percentile_over_long
            value_dict['long_ratio_of_cost_26to50_percentile_over_long'] = long_ratio_of_cost_26to50_percentile_over_long
            value_dict['long_ratio_of_cost_51to75_percentile_over_long'] = long_ratio_of_cost_51to75_percentile_over_long
            value_dict['long_ratio_of_cost_76to100_percentile_over_long'] = long_ratio_of_cost_76to100_percentile_over_long

            short_ratio_of_cost_0to25_percentile_list = len(cost_0to25_percentile_list_short) / cost_0to25_percentile_list_len if cost_0to25_percentile_list_len != 0 else 0
            short_ratio_of_cost_26to50_percentile_list = len(cost_26to50_percentile_list_short) / cost_26to50_percentile_list_len if cost_26to50_percentile_list_len != 0 else 0
            short_ratio_of_cost_51to75_percentile_list = len(cost_51to75_percentile_list_short) / cost_51to75_percentile_list_len if cost_51to75_percentile_list_len != 0 else 0
            short_ratio_of_cost_76to100_percentile_list = len(cost_76to100_percentile_list_short) / cost_76to100_percentile_list_len if cost_76to100_percentile_list_len != 0 else 0

            value_dict['short_ratio_of_cost_0to25_percentile_list'] = short_ratio_of_cost_0to25_percentile_list
            value_dict['short_ratio_of_cost_26to50_percentile_list'] = short_ratio_of_cost_26to50_percentile_list
            value_dict['short_ratio_of_cost_51to75_percentile_list'] = short_ratio_of_cost_51to75_percentile_list
            value_dict['short_ratio_of_cost_76to100_percentile_list'] = short_ratio_of_cost_76to100_percentile_list

            short_ratio_of_cost_0to25_percentile_over_all_records = len(cost_0to25_percentile_list_short) / cost_list_len if cost_list_len != 0 else 0
            short_ratio_of_cost_26to50_percentile_over_all_records = len(cost_26to50_percentile_list_short) / cost_list_len if cost_list_len != 0 else 0
            short_ratio_of_cost_51to75_percentile_over_all_records = len(cost_51to75_percentile_list_short) / cost_list_len if cost_list_len != 0 else 0
            short_ratio_of_cost_76to100_percentile_over_all_records = len(cost_76to100_percentile_list_short) / cost_list_len if cost_list_len != 0 else 0

            value_dict['short_ratio_of_cost_0to25_percentile_over_all_records'] = short_ratio_of_cost_0to25_percentile_over_all_records
            value_dict['short_ratio_of_cost_26to50_percentile_over_all_records'] = short_ratio_of_cost_26to50_percentile_over_all_records
            value_dict['short_ratio_of_cost_51to75_percentile_over_all_records'] = short_ratio_of_cost_51to75_percentile_over_all_records
            value_dict['short_ratio_of_cost_76to100_percentile_over_all_records'] = short_ratio_of_cost_76to100_percentile_over_all_records

            short_ratio_of_cost_0to25_percentile_over_short = len(cost_0to25_percentile_list_short) / cost_list_short_len if cost_list_short_len != 0 else 0
            short_ratio_of_cost_26to50_percentile_over_short = len(cost_26to50_percentile_list_short) / cost_list_short_len if cost_list_short_len != 0 else 0
            short_ratio_of_cost_51to75_percentile_over_short = len(cost_51to75_percentile_list_short) / cost_list_short_len if cost_list_short_len != 0 else 0
            short_ratio_of_cost_76to100_percentile_over_short = len(cost_76to100_percentile_list_short) / cost_list_short_len if cost_list_short_len != 0 else 0

            value_dict['short_ratio_of_cost_0to25_percentile_over_short'] = short_ratio_of_cost_0to25_percentile_over_short
            value_dict['short_ratio_of_cost_26to50_percentile_over_short'] = short_ratio_of_cost_26to50_percentile_over_short
            value_dict['short_ratio_of_cost_51to75_percentile_over_short'] = short_ratio_of_cost_51to75_percentile_over_short
            value_dict['short_ratio_of_cost_76to100_percentile_over_short'] = short_ratio_of_cost_76to100_percentile_over_short

            sql = 'select * from {}.{} where trade_time = {}'.format(
                FEATURES_SCHEMA,
                FEATURES_TABLE,
                now_date.strftime("%Y%m%d%H%M%S")
            )
            result, msg = execute_sql(db_info_features, 'select', sql)
            write_in_log(ANALYSIS_LOG_FILE_PATH, sql)
            if result:
                # check whether updating is needed
                id = result[0].pop('id')
                exist_value_list = [value for key, value in result[0].items()]
                if exist_value_list != [value if key != 'trade_time' else datetime.strptime(value, '%Y%m%d%H%M%S') for key, value in value_dict.items()]:
                    # update
                    if len(sorted(TRADES_DATA_ANALYSIS_FEATURES)) == len(sorted(list(value_dict.keys()))):
                        print('updating')
                        sql = 'update {}.{} set {} where id={}'.format(
                            FEATURES_SCHEMA,
                            FEATURES_TABLE,
                            ','.join([key + '=' + str(value) if key != 'trade_time' else key + '="' + str(value) + '"' for key, value in value_dict.items()]),
                            id
                        )
                        result, msg = execute_sql(db_info_features, 'update', sql)
                        write_in_log(ANALYSIS_LOG_FILE_PATH, msg)
                    else:
                        raise ValueError("number of value is not same with request features length")
            else:
                # insert new data
                if len(sorted(TRADES_DATA_ANALYSIS_FEATURES)) == len(sorted(list(value_dict.keys()))):
                    print('inserting')
                    sql = 'insert into {}.{} ({}) values ({})'.format(
                        FEATURES_SCHEMA,
                        FEATURES_TABLE,
                        ','.join(list(value_dict.keys())),
                        ','.join([str(value) if key != 'trade_time' else '"' + value + '"' for key, value in value_dict.items()])
                    )
                    result, msg = execute_sql(db_info_features, 'insert', sql)
                    write_in_log(ANALYSIS_LOG_FILE_PATH, msg)
                else:
                    raise ValueError("number of value is not same with request features length")
            print('finish to analyse trades data of {}'.format(trades_date))