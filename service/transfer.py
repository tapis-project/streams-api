
#from tapipy.actors import get_context
from flask import g, Flask, request
from service import meta
from service import influx
from zipfile import ZipFile
from datetime import datetime, timezone
from datetime import timedelta
import json
import pandas as pd
app = Flask(__name__)

from service import auth
from common import utils, errors
from common.logs import get_logger
logger = get_logger(__name__)
from common.config import conf
import sys
import os
from tapipy.tapis import Tapis

t = auth.t

def transfer_to_system(name,system_id, path, instrument_id, data_format, start_date, end_date):
    logger.debug("in transfer_to_system")
    index_result = meta.fetch_instrument_index(instrument_id)
    if index_result > 0:
        instrument = meta.get_instrument(index_result['project_id']index_result['site_id'],index_result['instrument_id'])
        if instrument:
            logger.debug(instrument)
            js= influx.query_measurments([{"inst":str(instrument['chords_id'])}])
            logger.debug(js)
            if len(js) > 1 and len(js['series']) > 0:
                df = pd.DataFrame(js['series'][0]['values'],columns=js['series'][0]['columns'])
                pv = df.pivot(index='time', columns='var', values=['value'])
                df1 = pv
                df1.columns = df1.columns.droplevel(0)
                df1 = df1.reset_index().rename_axis(None, axis=1)
                replace_cols = {}
                logger.debug(site)
                for v in instrument['variables']:
                    logger.debug(v)
                    replace_cols[str(v['chords_id'])]=v['var_id']
                df1.rename(columns=replace_cols,inplace=True)
                df1.set_index('time',inplace=True)
                if data_format == "csv":
                    logger.debug("CSV")
                    result = df1.to_csv()
                    metric = {'created_at':datetime.now().isoformat(),'type':'transfer','project_id':project_id,'username':g.username,'size': sys.getsizeof(result)}
                    metric_result, metric_bug =auth.t.meta.createDocument(db=conf.tenant[g.tenant_id]['stream_db'], collection='streams_metrics', request_body=metric, _tapis_debug=True)
                    logger.debug(metric_result)
                    filename = name+'.csv'
                else:
                    result = json.loads(df1.to_json())
                    result['measurements_in_file'] = len(df1.index)
                    result['instrument'] = instrument
                    site.pop('instruments',None)
                    result['site'] = meta.strip_meta(site)
                    metric = {'created_at':datetime.now().isoformat(),'type':'transfer','project_id':project_id,'username':g.username,'size': str(sys.getsizeof(result))}
                    metric_result, metric_bug =auth.t.meta.createDocument(db=conf.tenant[g.tenant_id]['stream_db'], collection='streams_metrics', request_body=metric, _tapis_debug=True)
                    logger.debug(metric_result)
                    filename = name+'.json'
                logger.debug(filename)
                with open(filename, 'w') as f:
                    f.write(result)
                f.close()
                #upload file to system at the path
                t.access_token = t.service_tokens['admin']['access_token']
                t.x_username= g.username
                t.x_tenant_id = g.tenant_id
                msg = ""
                msg = t.upload(source_file_path=filename, system_id=system_id, dest_file_path=path+'/'+filename)
                logger.debug(msg)
                os.remove(filename) #cleanup zipfile
                return msg
            else:
        else:
