
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
from tapipy.tapis import Tapis

t = auth.t

def archive_to_system(system_id, path, project_id, archive_type, data_format):
    logger.debug("in archive_to_system")
    start_date= (datetime.now() - timedelta(days=10000)).isoformat()#'1980-01-01T00:00:00.0'
    end_date = datetime.now().isoformat()
    file_list = []
    archive_date = datetime.now()
    project = meta.get_project(project_id = project_id)[0]
    logger.debug(project)
    sites = meta.list_sites(project_id = project_id)[0]
    #logger.debug(sites)
    #print(sites)
    for site in sites:
        logger.debug(site)
        if 'instruments' in site:
            instruments = site['instruments']
            for instrument in instruments:
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
                    #logger.debug(replace_cols)
                    df1.rename(columns=replace_cols,inplace=True)
                    df1.set_index('time',inplace=True)
                    if data_format == "csv":
                        logger.debug("CSV")
                        result = df1.to_csv()
                        metric = {'created_at':datetime.now().isoformat(),'type':'archive','project_id':project_id,'username':g.username,'size': sys.getsizeof(result)}
                        metric_result, metric_bug =auth.t.meta.createDocument(db=conf.tenant[g.tenant_id]['stream_db'], collection='streams_metrics', request_body=metric, _tapis_debug=True)
                        logger.debug(metric_result)
                    else:
                        result = json.loads(df1.to_json())
                        result['measurements_in_file'] = len(df1.index)
                        result['instrument'] = instrument
                        site.pop('instruments',None)
                        result['site'] = meta.strip_meta(site)
                        metric = {'created_at':datetime.now().isoformat(),'type':'archive','project_id':project_id,'username':g.username,'size': str(sys.getsizeof(result))}
                        metric_result, metric_bug =auth.t.meta.createDocument(db=conf.tenant[g.tenant_id]['stream_db'], collection='streams_metrics', request_body=metric, _tapis_debug=True)
                        logger.debug(metric_result)
                # result = meta.list_measurements(inst_id=instrument_id,
                #                                             project_uuid=project_id,
                #                                             site_id=site_id,
                #                                             start_date='1900-01-01T00:00:00Z',
                #                                             end_date='2025-12-30T22:19:25Z',
                #                                             format='csv')
                filename = instrument['inst_name']+'_'+archive_date.isoformat()+'.csv'
                logger.debug(filename)
                with open(filename, 'w') as f:
                    f.write(result)
                f.close()
                file_list.append(filename)
    logger.debug("WRITE METADATA FILE")
    meta_filename = project_id+"_"+'medata_'+archive_date.isoformat()+'.json'
    with open(meta_filename, 'w') as f:
        project['sites'] = sites
        f.write(json.dumps(project))
    f.close()
    file_list.append(meta_filename)
    if (archive_type == "zip"):
        #create zip archive
        print("zip")
        zipfilename = project_id+"_"+archive_date.isoformat()+'.zip'
        zipObj = ZipFile(zipfilename, 'w')
        for f in file_list:
            # Add multiple files to the zip
            zipObj.write(f)
        # close the Zip File
        zipObj.close()
    else:
      #create tar
      print('tar')

    #upload file to system at the path
    t.access_token = t.service_tokens['admin']['access_token']
    t.x_username= g.username
    t.x_tenant_id = g.tenant_id
    msg = ""
    msg = t.upload(source_file_path=zipfilename, system_id=system_id, dest_file_path=path+'/'+zipfilename)
    logger.debug(msg)
    return msg
# context = get_context()
# message = context['raw_message']
#archive_to_system(message['system_id'], message['path'], message['project_id'], message['archive_type'])
