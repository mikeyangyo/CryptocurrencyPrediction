import argparse

from datetime import datetime

def dateChecking(requiredDate):
    try:
        return datetime.strptime(requiredDate, '%Y-%m-%d')
    except ValueError:
        msg = 'Not a valid date: {0}'.format(requiredDate)
        raise argparse.ArgumentTypeError(msg)