import datetime
import enum
import requests
import json
import time
import pandas as pd
from flask import g, Flask
from tapisservice.config import conf
app = Flask(__name__)

from tapisservice import errors
# get the logger instance -
from tapisservice.logs import get_logger
logger = get_logger(__name__)

from influxdb_client import InfluxDBClient
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
                    try:
                        value = float(itm[k])
                        measurement = "tsdata"
                    except ValueError:
                        value = str(itm[k])
                        measurement = "nonfloat"

                    json_body.append(
                        {
                            "measurement": measurement,
                            "tags": {
                                "site": site_id,
                                "inst": instrument['chords_id'],
                                "var": inst_vars[k]
                            },
                            "time": itm['datetime'],
                            "fields": {
                                "value": value
                            }
                        }
                    )
                    if k in return_body:
                        return_body[k].append({itm['datetime']: value})
                    else:
                        return_body[k] = [{itm['datetime']: value}]

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
        logger.debug(json_body)
        result = write_api.write(bucket=bucket_name, record=json_body)
        logger.debug(result)
    return {'resp':result,'msg':'','body':return_body}

#expects a list of fields {key:value} to build and AND query to influxdb to fetch CHORDS measurments
def query_measurments(bucket_name, query_field_list):
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
    from time import process_time 
    import requests
    tic = time.perf_counter()

#     url --request -G http://localhost:8086/query?orgID=INFLUX_ORG_ID&database=MyDB&retention_policy=MyRP \
#   --header 'Authorization: Token INFLUX_TOKEN' \
#   --header 'Accept: application/csv' \
#   --header 'Content-type: application/json' \
#   --header 'Accept-Encoding: gzip' \
#   --data-urlencode "q=SELECT used_percent FROM example-db.example-rp.example-measurement WHERE host=host1"
    import csv

    # Define the InfluxDB2 API URL, token, organization, and bucket
    url = "http://"+conf.influxdb_host+":"+conf.influxdb_port+"/api/v2/query"
    org = "tapis"
    bucket = bucket_name

    # Define the Flux query to get data from the bucket
    #query = f'from(bucket: "{bucket}") |> range(start: -1h)'
    query= query + '|> drop(columns: ["_start", "_stop", "_field","_measurement","inst","site","result","table"])|> pivot(rowKey:["_time"], columnKey: ["var"], valueColumn: "_value")'

    # Define the headers for the API request, including the token and the content type
    headers = {
        "Authorization": f"Token {conf.influxdb_token}",
        "Content-type": "application/vnd.flux",
        "Accept": "text/csv"
    }
    params ={"org":org}

    # Send a POST request to the API with the query and the headers
    response = requests.post(url, data=query, headers=headers,params=params)
    logger.debug(response)
    toc = time.perf_counter()
    logger.debug(f"Downloaded  in {toc - tic:0.4f} seconds")
    import pandas as pd
    from io import StringIO
    input = StringIO(response.text)
    result = pd.read_csv(input, index_col=0)
    # with InfluxDBClient(url=conf.influxdb_host+':'+conf.influxdb_port, token=conf.influxdb_token, org=conf.influxdb_org) as client:
    #     result = client.query_api().query(query=query)#,data_frame_index=['_time'])
    # toc = time.perf_counter()
    # logger.debug(f"Downloaded  in {toc - tic:0.4f} seconds")
    # logger.debug(result)
    # #logger.debug(result.to_values())    
    # if influx measurements include value that are stored as strings
    # if isinstance(result, list):
    #     for i in result:
    #         i.drop("_measurement", axis=1, inplace=True)
    #     merged_df = pd.concat([result[0], result[1]], axis=0)
    #     #logger.debug(merged_df)
    #     return merged_df

    #logger.debug(result)
    return result

def ping():
    headers = {
        'content-type': "application/json"
    }
    res = requests.get(conf.influxdb_host + ':' + conf.influxdb_port +'/health',  verify=False)
    return res.status_code
