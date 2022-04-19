
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
from tapisservice import errors
from tapisservice.logs import get_logger
logger = get_logger(__name__)
from tapisservice.config import conf
import sys
import os
from tapipy.tapis import Tapis

t = auth.t

def transfer_to_system(filename, system_id, path, project_id, instrument_id, data_format, start_date, end_date):
    logger.debug("in transfer_to_system")
    index_result = meta.fetch_instrument_index(instrument_id)
    if "project_id" in index_result:
        site = meta.get_site(index_result['project_id'],index_result['site_id'])[0]
        instrument = meta.get_instrument(index_result['project_id'],index_result['site_id'],index_result['instrument_id'])[0]
        project = meta.get_project(project_id=project_id)
        if instrument:
            logger.debug("CHORDS_ID: "+str(instrument['chords_id']))
            logger.debug(start_date)
            logger.debug(end_date)
            if 'bucket' in project:
                bucket_name=project.project_id
            else:
                bucket_name=conf.influxdb_bucket
            js= influx.query_measurments(bucket_name=bucket_name,query_field_list=[{'inst':str(instrument['chords_id'])},{'start_date': str(start_date)},{'end_date': str(end_date)}])
            #logger.debug(js)
            if len(js) > 1 and len(js['series']) > 0:
                df = pd.DataFrame(js['series'][0]['values'],columns=js['series'][0]['columns'])
                pv = df.pivot(index='time', columns='var', values=['value'])
                df1 = pv
                df1.columns = df1.columns.droplevel(0)
                df1 = df1.reset_index().rename_axis(None, axis=1)
                replace_cols = {}
                for v in instrument['variables']:
                    logger.debug(v)
                    replace_cols[str(v['chords_id'])]=v['var_id']
                df1.rename(columns=replace_cols,inplace=True)
                df1.set_index('time',inplace=True)
                if data_format == "csv":
                    logger.debug("CSV")
                    result = df1.to_csv()
                    metric = {'created_at':datetime.now().isoformat(),'type':'transfer','project_id':project_id,'username':g.username,'size': sys.getsizeof(result)}
                else:
                    result = json.loads(df1.to_json())
                    result['measurements_in_file'] = len(df1.index)
                    result['instrument'] = instrument
                    site.pop('instruments',None)
                    result['site'] = meta.strip_meta(site)
                    metric = {'created_at':datetime.now().isoformat(),'type':'transfer','project_id':project_id,'username':g.username,'size': str(sys.getsizeof(result))}
                metric['request'] = {"filename":filename, "sytem_id":system_id, "path":path, "project_id":project_id,
                                     "inst_id":instrument_id, "data_format":data_format, "start_date":start_date, "end_date":end_date}
                metric_result, metric_bug =t.meta.createDocument(_tapis_set_x_headers_from_service=True,db=conf.tenant[g.tenant_id]['stream_db'], collection='streams_metrics', request_body=metric, _tapis_debug=True)
                logger.debug(filename)
                with open(filename, 'w') as f:
                    f.write(json.dumps(result))
                f.close()
                #upload file to system at the path
                t.access_token = t.service_tokens['admin']['access_token']
                t.x_username= g.username
                t.x_tenant_id = g.tenant_id
                msg = ""
                msg = t.upload(source_file_path=filename, system_id=system_id, dest_file_path=path+'/'+filename)
                logger.debug(msg)
                os.remove(filename) #cleanup zipfile
                metric['transfer_status'] = msg
                return metric
            else:
                msg="No Measurements Founds"
                return msg
        else:
            msg = "Transfer Failed! Instrument not found with ID: "+ instrument_id
            return msg
