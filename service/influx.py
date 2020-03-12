import datetime
import enum
import requests
import json
from flask import g, Flask
from common.config import conf
app = Flask(__name__)

from common import utils, errors
# get the logger instance -
from common.logs import get_logger
logger = get_logger(__name__)

from influxdb import InfluxDBClient

influx_client = InfluxDBClient(host=conf.influxdb_host, port=conf.influxdb_port, database=conf.influxdb_database)

def create_database(database_name):
    result = influx_client.create_database(database_name)
    return result

def create_measurement(payload):
    result = influx_client.write_points(payload)
    return result

def query_measuremnts(query):
    #logger.debug(query.get('q'))
    result = influx_client.query(query.get('q')) #"SELECT \"value\" FROM \"cpu_load_short\" WHERE \"region\"='us-west'")
    return result.raw

def list_measurements(instrument_id):
    print(something)
