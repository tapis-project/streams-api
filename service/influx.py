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

from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

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
    logger.debug(result)
    return result

def compact_write_measurements(site_id, instrument, body):
    json_body=[]
    return_body={}
    inst_vars = {}
    logger.debug(instrument)
    for v in instrument['variables']:
        inst_vars[v['var_id']]= v['chords_id']
    logger.debug(inst_vars)
    for itm in body['vars']:
        logger.debug(itm)
        #make sure the user defined variable ids ex
        for k in itm:
            logger.debug(k)
            if k != 'datetime':
                logger.debug('not datetime')
                if k in inst_vars and 'datetime' in itm:
                    json_body.append(
                        {
                            "measurement": "tsdata",
                            "tags": {
                                "site": site_id,
                                "inst": instrument['chords_id'],
                                "var": inst_vars[k]
                            },
                            "time": itm['datetime'],
                            "fields": {
                                "value": float(itm[k])
                            }
                        }
                    )
                    if k in return_body:
                        return_body[k].append({itm['datetime']: float(itm[k])})
                    else:
                        return_body[k] = [{itm['datetime']: float(itm[k])}]

                else:
                    msg = 'Datetime field required and it is missing!'
                    if 'datetime' in itm:
                         msg = 'Variable ID: '+k+' is invalid!'
                    logger.debug(msg)
                    return {'resp':False,'msg':msg}
    logger.debug(json_body)
    with InfluxDBClient(host=conf.influxdb_host+':'+conf.influxdb_port, token=conf.influxdb_token, org=conf.influxdb_org) as client:
        write_api = client.write_api(write_options=SYNCHRONOUS)
        result = write_api.write(bucket=conf.influxdb_bucket, record=json_body)
    return {'resp':result,'msg':'','body':return_body}

def write_measurements(site_id, instrument, body):
    json_body=[]
    inst_vars = {}
    logger.debug(instrument)
    for v in instrument['variables']:
        inst_vars[v['var_id']]= v['chords_id']
    logger.debug(inst_vars)
    for itm in body['vars']:
        #make sure the user defined variable ids ex
        if itm['var_id'] in inst_vars:
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
        else:
            return {'resp':False,'msg':'Variable ID: '+itm['var_id']+' is invalid!'}
    logger.debug(json_body)
    with InfluxDBClient(host=conf.influxdb_host+':'+conf.influxdb_port, token=conf.influxdb_token, org=conf.influxdb_org) as client:
            write_api = client.write_api(write_options=SYNCHRONOUS)
            result = write_api.write(bucket=conf.influxdb_bucket, record=json_body)
    return {'resp':result,'msg':''}

#expects a list of fields {key:value} to build and AND query to influxdb to fetch CHORDS measurments
def query_measurments(query_field_list):
    logger.debug("IN INFLUX QUERY")
    for fields in query_field_list:
        #fields = json.loads(itm)
        print(fields)
        for k in fields:
            if k == "start_date":
                if str(fields[k]) != 'None':
                    start=str(fields[k])
            elif k == "end_date":
                if str(fields[k]) != 'None':
                    stop=str(fields[k])
            else:
                query_list.append('r["'+k+'"]=="'+str(fields[k])+'"')
    query_filters = ' and '.join(query_list)
    query = 'from(bucket: "'+conf.influxdb_bucket+'")'+'''
    |> range(start: ''' +start+' stop:'+ stop+''' )
    |> filter(fn: (r) => '''+query_fileters+')'
    logger.debug(query)
    with InfluxDBClient(host=conf.influxdb_host+':'+conf.influxdb_port, token=conf.influxdb_token, org=conf.influxdb_org) as client:
        result = client.query_api().query_raw(query)
    logger.debug(result)
    return result.raw

def fetch_archive_measurements(query_field_list):
    logger.debug("IN INFLUX QUERY")
    base_query = "SELECT * FROM \"tsdata\" WHERE "
    query_list=[];
    for fields in query_field_list:
        #fields = json.loads(itm)
        print(fields)
        for k in fields:
            query_list.append("\""+k+"\"='"+str(fields[k])+"' ")

    query_where = ' AND '.join(query_list)
    logger.debug(base_query+query_where)
    result = influx_client.query(base_query+query_where)
    logger.debug(result)
    return result.raw

def list_measurements(instrument_id):
    #curl -G 'http://localhost:8086/query?pretty=true' --data-urlencode "db=mydb" --data-urlencode "q=SELECT \"value\" FROM \"cpu_load_short\" WHERE \"region\"='us-west'"
    print(something)
    logger.debug("IN List Measurements")
    headers = {
        'content-type': "application/json"
    }
    query = "q=SELECT * FROM \"tsdata\" WHERE "
    url = urllib.parse.quote(conf.influxdb_host+":"+conf.influxdb_port+'query?', safe='')
    res = requests.post(conf.influxdb_host+":"+conf.influxdb_port+'query?', json=body, headers=headers,auth=HTTPBasicAuth(conf.kapacitor_username, conf.kapacitor_password), verify=False)
    logger.debug('Kapacitor Response' + str(res.content))
    logger.debug('status_code'+ str(res.status_code))
    return json.loads(res.content),res.status_code

def ping():
    headers = {
        'content-type': "application/json"
    }
    res = requests.get('http://'+conf.influxdb_host + ':' + conf.influxdb_port +'/ping',  verify=False)
    return res.status_code
