import datetime
import enum
import requests
import json
from flask import g, Flask
from tapisservice.config import conf
app = Flask(__name__)
import logging
import sys
import csv
import time

from tapisservice import errors
# get the logger instance -
from tapisservice.logs import get_logger
logger = get_logger(__name__)

from influxdb_client import InfluxDBClient, Dialect
from influxdb_client.client.write_api import SYNCHRONOUS

def create_project_bucket(bucket_name):
    #create a bucket name that is the same as the project_id
    logger.debug("In Create Project Bucket")
    with InfluxDBClient(url=conf.influxdb_host+':'+conf.influxdb_port, token=conf.influxdb_token) as client:
        buckets_api = client.buckets_api()
        created_bucket = buckets_api.create_bucket(bucket_name=bucket_name, org=conf.influxdb_org)
        logger.debug(created_bucket)
        if created_bucket.created_at:
            return True
        else:
            return False

def compact_write_measurements(bucket_name, site_id, instrument, body):
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
    #logger.debug(json_body)
    with InfluxDBClient(url=conf.influxdb_host+':'+conf.influxdb_port, token=conf.influxdb_token, org=conf.influxdb_org) as client:
        write_api = client.write_api(write_options=SYNCHRONOUS)
        logger.debug(bucket_name)
        result = write_api.write(bucket=bucket_name, record=json_body)
        logger.debug(json_body)
        logger.debug(result)
    return {'resp':result,'msg':'','body':return_body}

#expects a list of fields {key:value} to build and AND query to influxdb to fetch CHORDS measurments
def query_measurments(bucket_name, query_field_list):
    start_time = time.perf_counter()
    logger.debug("IN INFLUX QUERY: ")
    query_list=[]
    variable_list=[]
    start=''
    stop=''
    limit=''
    offset=''
    for fields in query_field_list:
        #fields = json.loads(itm)
        logger.debug(fields)
        for k in fields:
            if k == "start_date":
                if str(fields[k]) != 'None':
                    start=str(fields[k])
            elif k == "end_date":
                if str(fields[k]) != 'None':
                    stop=str(fields[k])
            elif k == "limit":
                if str(fields[k]) != 'None':
                    limit=str(fields[k])
            elif k == "offset":
                if str(fields[k]) != 'None':
                    offset=str(fields[k])
            elif k == "var":
                variable_list.append('r["'+k+'"]=="'+str(fields[k])+'"')
            else:
                query_list.append('r["'+k+'"]=="'+str(fields[k])+'"')
    if len(variable_list) > 0:
        query_filters = ' and '.join(query_list) + ' and ' + ' or '.join(variable_list)
    else:
        query_filters = ' and '.join(query_list)

    query = 'from(bucket: "'+bucket_name+'")'
    if start !='' and stop!='':
        query = query + '\n|> range(start: '+start+', stop:'+ stop+' )'
    elif start !='':
        query = query + '\n|> range(start: '+start+' )'
    elif stop!='':
        query = query + '\n|> range(start: 0, stop:'+ stop+' )'
    else:
        query = query + '|> range(start: 0)'
    query = query +'|> filter(fn: (r) => '+query_filters+') |> sort(columns: ["_time"], desc: false)'
    if limit != '' and offset != '':
        query = query +'|> limit(n: '+limit+', offset: '+offset+')'
    elif limit != '':
        query = query +'|> limit(n: '+limit+')'
    elif offset !='':
        query = query +'|> limit(offset: '+offset+')'
    logger.debug(query)
    with InfluxDBClient(url=conf.influxdb_host+':'+conf.influxdb_port, token=conf.influxdb_token, org=conf.influxdb_org) as client:
        # for _, db_logger in client.conf.loggers.items():
        #     db_logger.setLevel(logging.DEBUG)
        #     db_logger.addHandler(logging.StreamHandler(sys.stdout))
        result = client.query_api().query_data_frame(query)
    logger.debug(result.to_string())
    end_time = time.perf_counter()
    logger.debug(f"Elapsed Time for query: ${end_time-start_time} seconds")
    return result

def query_measurements_csv(bucket_name, query_field_list):
    start_time = time.perf_counter()
    logger.debug("IN INFLUX QUERY: ")
    query_list=[]
    variable_list=[]
    rename_list = {}
    start=''
    stop=''
    limit=''
    offset=''
    for fields in query_field_list:
        #fields = json.loads(itm)
        logger.debug(fields)
        for k in fields:
            if k == "start_date":
                if str(fields[k]) != 'None':
                    start=str(fields[k])
            elif k == "end_date":
                if str(fields[k]) != 'None':
                    stop=str(fields[k])
            elif k == "limit":
                if str(fields[k]) != 'None':
                    limit=str(fields[k])
            elif k == "offset":
                if str(fields[k]) != 'None':
                    offset=str(fields[k])
            elif k == "var":
                variable_list.append('r["'+k+'"]=="'+str(fields[k])+'"')
            elif k == "rename":
                rename_list = fields[k]
                rename_list["_time"] = "time"
            else:
                query_list.append('r["'+k+'"]=="'+str(fields[k])+'"')
    if len(variable_list) > 0:
        query_filters = ' and '.join(query_list) + ' and ' + ' or '.join(variable_list)
    else:
        query_filters = ' and '.join(query_list)

    query = 'from(bucket: "'+bucket_name+'")'
    if start !='' and stop!='':
        query = query + '\n|> range(start: '+start+', stop:'+ stop+' )'
    elif start !='':
        query = query + '\n|> range(start: '+start+' )'
    elif stop!='':
        query = query + '\n|> range(start: 0, stop:'+ stop+' )'
    else:
        query = query + '|> range(start: 0)'
    query = query +'|> filter(fn: (r) => '+query_filters+') |> sort(columns: ["_time"], desc: false)'
    if limit != '' and offset != '':
        query = query +'|> limit(n: '+limit+', offset: '+offset+')'
    elif limit != '':
        query = query +'|> limit(n: '+limit+')'
    elif offset !='':
        query = query +'|> limit(offset: '+offset+')'
    query = query + '|> pivot(rowKey: ["_time"], columnKey: ["var"], valueColumn: "_value")'
    query = query + '|> drop(columns: ["_start", "_stop", "_measurement", "_field", "inst", "site"])'
    query = query + '|> rename(columns: ' + str(rename_list).replace("\'", "\"") +')'
    logger.debug(query)
    with InfluxDBClient(url=conf.influxdb_host+':'+conf.influxdb_port, token=conf.influxdb_token, org=conf.influxdb_org) as client:
        influx_result = client.query_api().query_csv(query, dialect=Dialect(header=True, annotations=[], delimiter=","))

        lists = influx_result.to_values()
        lists = [l[3:] for l in lists]

        for l in lists[1:]:
            l[0] = l[0].replace('T', ' ').replace('Z', '+00:00')

        # Create csv output string
        output = csv.StringIO()
        writer = csv.writer(output)
        writer.writerows(lists)

        result = output.getvalue()
    logger.debug(result)
    end_time = time.perf_counter()

    elapsed_string = str(end_time-start_time)
    logger.debug("Elapsed Time for query: " + elapsed_string)
    return result

def ping():
    headers = { 
        'content-type': "application/json"
    }
    res = requests.get(conf.influxdb_host + ':' + conf.influxdb_port +'/health',  verify=False)
    return res.status_code
