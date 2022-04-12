import requests
import json
from flask import g, Flask, request, make_response
from common.config import conf
from common import auth
import datetime
app = Flask(__name__)

from common import utils, errors
from service import auth
from service import chords
# get the logger instance -
from common.logs import get_logger
logger = get_logger(__name__)

from service import influx
import pandas as pd
import sys
from datetime import datetime
from io import StringIO

def fetch_measurement_dataframe(instrument, request):
    influx_query_input = [{"inst":str(instrument['chords_id'])}]
    if request.args.get('start_date'):
        influx_query_input.append({"start_date": request.args.get('start_date')})
    if request.args.get('end_date'):
        influx_query_input.append({"end_date": request.args.get('end_date')})    
    if request.args.get('limit'):
        influx_query_input.append({"limit": request.args.get('limit')}) 
    if request.args.get('offset'):
        influx_query_input.append({"offset": request.args.get('offset')}) 
    return influx.query_measurments( influx_query_input)

def create_csv_response(df1,project_id):
    logger.debug("CSV")
    logger.debug(f"CSV in Bytess: "+ str(sys.getsizeof(df1.to_csv)))
    output = make_response(df1.to_csv())
    output.headers["Content-Disposition"] = "attachment; filename=export.csv"
    output.headers["Content-type"] = "text/csv"
    metric = {'created_at':datetime.now().isoformat(),'type':'download','project_id':project_id,'username':g.username,'size': sys.getsizeof(df1.to_csv)}
    metric_result, metric_bug =auth.t.meta.createDocument(db=conf.tenant[g.tenant_id]['stream_db'], collection='streams_metrics', request_body=metric, _tapis_debug=True)
    logger.debug(f' Metric result: ' +str(metric_result))
    return output

def create_json_response(df1, project_id, instrument, params):
    if df1.empty:
        result={}
        result['measurements_in_file']=0
    else:
      df2 = pd.read_csv(StringIO(df1.to_csv()),index_col="time")
      result = json.loads(df2.to_json())
      result['measurements_in_file'] = len(df2.index)
    logger.debug(result)
    if 'with_metadata' in params:
        if params['with_metadata'] == 'True':
            result['instrument'] = instrument
            site.pop('instruments',None)
            result['site'] = meta.strip_meta(site)
    logger.debug("JSON in Bytes: "+ str(sys.getsizeof(result)))
    metric = {'created_at':datetime.now().isoformat(),'type':'download','project_id':project_id,'username':g.username,'size': sys.getsizeof(result)}
    metric_result, metric_bug =auth.t.meta.createDocument(db=conf.tenant[g.tenant_id]['stream_db'], collection='streams_metrics', request_body=metric, _tapis_debug=True)
    logger.debug(metric_result)
    return result
