from flask import Flask, request
from flask_restful import Resource, Api
from json import dumps
from datetime import datetime
from pymysql import connect, ProgrammingError
from pymysql.cursors import DictCursor


app = Flask(__name__)
api = Api(app)

db_info_trades = {
    'host' : '140.118.126.136',
    'user_name' : '123',
    'passwd' : '1234567890',
    'db' : 'web_acess'
}

SCHEMA = 'web_acess'

class Predict_Data(Resource):
    def get(self):
        db_connect = connect(
            host = db_info_trades['host'],
            user = db_info_trades['user_name'],
            password = db_info_trades['passwd'],
            db = db_info_trades['db']
        )
        print(request.args)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        currency_type = request.args.get('currency_type')
        model_type = int(request.args.get('model_type'))
        last_trading_date = request.args.get('last_trading_date')
        result = None
        if model_type == 1:
            table_name = 'yesterday_lstm_' + currency_type.lower()
            sql = 'select * from {}.{} where DATE BETWEEN "{}" AND "{}"'.format(SCHEMA, table_name, datetime.strptime(start_date, "%Y-%m-%d").strftime("%Y-%m-%d"), datetime.strptime(end_date, "%Y-%m-%d").strftime("%Y-%m-%d"))
            print(sql)
            with db_connect.cursor(DictCursor) as cursor:
                try:
                    result = cursor.execute(sql)
                    result = cursor.fetchall()
                except Exception as e:
                    print("Error: Unable to fetch data", e)
                    raise ProgrammingError
                db_connect.close()
        return result
        

api.add_resource(Predict_Data, '/api/predict_data')


if __name__ == '__main__':
     app.run(port=8000)