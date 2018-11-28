__all__ = ['CRYPOTOCURRENCIES_ABBREV', 'MONEY_ABBREV', 'getUserListFromFile', 'execute_sql', 'get_now_time_string', 'check_double_quotes']

from pymysql import connect
from datetime import datetime

CRYPOTOCURRENCIES_ABBREV = {
    'Bitcoin' : 'btc',
    'Litecoin' : 'ltc',
    'EOS' : 'eos',
    'Bitcoin Cash' : 'bch',
    'Tether' : 'usdt',
    'Ripple' : 'xrp',
    'Vertcoin' : 'vtc',
    'Dogecoin' : 'doge',
    'Ethereum' : 'eth'
}

MONEY_ABBREV = {
    'U.S. Dollar' : 'usd'
}

def getUserListFromFile(filename = "./user_list.txt"):
    f = open(filename, 'r')
    rows = f.readlines()
    return [row.rstrip() for row in rows]

def execute_sql(db_info, operation_name, sql):
    connection = connect(
        host = db_info['host'],
        user = db_info['user_name'],
        password = db_info['passwd'],
        db = db_info['db']
    )

    try:
        result = None
        msgs = []
        successed = True
        with connection.cursor() as cursor:
            operation_name = operation_name.upper()
            if operation_name == "SELECT":
                try:
                    result = cursor.execute(sql)
                    result = cursor.fetchone()
                    successed = True
                except:
                    print("Error: Unable to fetch data")
                    successed = False
            
            elif operation_name == "UPDATE" or\
                 operation_name == "INSERT" or\
                 operation_name == "DELETE":
                try:
                    result = cursor.execute(sql)
                    connection.commit()
                    successed = True
                except:
                    connection.rollback()
                    successed = False
    finally:
        connection.close()
        if successed:
            msgs.append("[{}] {} Success\n".format(get_now_time_string(), operation_name))
        else:
            msgs.append("[{}] {} Fail\n".format(get_now_time_string(), operation_name))
        msgs.append("\tSQL : {}\n".format(sql))
        return result, msgs, successed

def write_in_log(file_location, msgs):
    with open(file_location, "a+") as fp:
        fp.writelines(msgs)
        fp.close()

def check_double_quotes(string):
    last_position = 0
    position = string.find('"', last_position)
    last_position = position
    while last_position != -1:
        string = string[:position] + '\\' + string[position:]
        position = string.find('"', last_position + 2)
        last_position = position
    return string

def get_now_time_string(format = '%Y/%m/%d %H%M%S'):
    return datetime.now().strftime(format)