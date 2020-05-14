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

influx_client = InfluxDBClient(host=conf.influxdb_host, port=conf.influxdb_port, username=conf.influxdb_username, password=conf.influxdb_password, database=conf.influxdb_database)

def create_database(database_name):
    result = influx_client.create_database(database_name)
    return result

def create_measurement(site_id,inst_id,var_id,value, timestamp):
    json_body = [
        {
            "measurement": "tsdata",
            "tags": {
                "site": site_id,
                "inst": inst_id,
                "var": var_id
            },
            "time": timestamp,
            "fields": {
                "value": value
            }
        }
    ]
    result = influx_client.write_points(json_body)
    return result

def write_measurements(site_id, instrument, body):
    json_body=[]
    inst_vars = {}
    logger.debug(instrument)
    for v in instrument['variables']:
        inst_vars[v['var_id']]= v['chords_id']
    logger.debug(inst_vars)
    for itm in body['vars']:
        json_body.append(
            {
                "measurement": "tsdata",
                "tags": {
                    "site": site_id,
                    "inst": instrument['chords_id'],
                    "var": inst_vars[itm['var_id']]
                },
                "time": body['datetime'],
                "fields": {
                    "value": float(itm['value'])
                }
            }
        )
    logger.debug(json_body)
    result = influx_client.write_points(json_body)
    return result

#expects a list of fields {key:value} to build and AND query to influxdb to fetch CHORDS measurments
def query_measurments(query_field_list):
    #logger.debug(query.get('q'))
    base_query = "SELECT * FROM \"tsdata\" WHERE "
    query_list=[];
    for itm in query_field_list:
        fields = json.loads(itm)
        for k in fields:
            # if k  "start_time":
            #     query_list.append("\"time\">='"+str(fields[k])+"' "
            # if k == "end_time":
            #     query_list.append("\"time\"<='"+str(fields[k])+"' "
            # else:
            query_list.append("\""+k+"\"='"+str(fields[k])+"' ")

    query_where = ' AND '.join(query_list)
    logger.debug(base_query+query_where)
    result = influx_client.query(base_query+query_where)
    return result.raw

def list_measurements(instrument_id):
    print(something)
