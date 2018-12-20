from funcy.flow import retry
from pymysql import connect, ProgrammingError
from pymysql.cursors import DictCursor
from datetime import datetime

def get_now_time_string(format = '%Y/%m/%d %H:%M:%S'):
    return datetime.now().strftime(format)

@retry(tries=5)
def execute_sql(db_info, operation_name, sql):
    connection = connect(
        host = db_info['host'],
        user = db_info['user_name'],
        password = db_info['passwd'],
        db = db_info['db']
    )
    sql = sql.encode('utf8')
    result = None
    msgs = []
    with connection.cursor(DictCursor) as cursor:
        operation_name = operation_name.upper()
        if operation_name == "SELECT":
            try:
                result = cursor.execute(sql)
                result = cursor.fetchall()
            except Exception as e:
                print("Error: Unable to fetch data", e)
                raise ProgrammingError
            
        elif operation_name == "UPDATE" or\
            operation_name == "INSERT" or\
            operation_name == "DELETE":
            try:
                result = cursor.execute(sql)
                connection.commit()
            except:
                connection.rollback()
                raise ProgrammingError

    connection.close()
    msgs.append("[{}] {} Success\n".format(get_now_time_string(), operation_name))
    msgs.append("\tSQL : {}\n".format(sql))
    return result, msgs

def write_in_log(file_location, msgs):
    with open(file_location, "a+") as fp:
        fp.writelines(msgs)
        fp.close()