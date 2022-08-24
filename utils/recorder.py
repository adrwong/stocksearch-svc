from datetime import datetime
import requests
from more_itertools import take
from distutils.log import INFO
import LoraLogger


session = requests.Session()
user = 'elastic'
password = 'dj7386e3YGPN38d7FK7mJDi8'
session.auth = (user, password)
end_point = 'http://192.168.1.152:9200'
auth = session.post(end_point)
logger = LoraLogger.logger(__name__, INFO)


def construct_data(input, datastream):
    constructed = input

    constructed['target_address'] = 'http://192.168.1.152:9200/'+datastream+'/'
    constructed['@timestamp'] = (datetime.utcnow() -
                                 datetime.utcfromtimestamp(0)).total_seconds() * 1000.0

    return constructed


def send(data, datastream, session=session):
    resp = session.post(
        url='http://192.168.1.152:9200/'+datastream+'/_doc', json=construct_data(data, datastream))

    return resp
