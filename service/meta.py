import enum
import requests
import json
from flask import g, Flask
from common.config import conf
app = Flask(__name__)

from common import utils, errors
from tapy.dyna import DynaTapy
# get the logger instance -
from common.logs import get_logger
logger = get_logger(__name__)

t = DynaTapy(base_url=conf.tapis_base_url, username=conf.streams_user, account_type=conf.streams_account_type, tenant_id=conf.tapis_tenant)
t.get_tokens()

# result=t.meta.createDocument(db='StreamsTACCDB', collection='Proj1', request_body={ "site_id" : 1234299, "lat" : 70.5, "lon" : 90, "instruments" : [ { "inst_id" : 2334, "inst_name" : "myinstrument", "variables" : [ { "var_id" : 34, "var_name" : "a", "abbrev" : "whatever", "unit" : "myunit" } ] }, { "inst_id" : 2435, "inst_name" : "myinstrument2","variables" : [ { "var_id" : 33, "var_name" : "a", "abbrev" : "whatever", "unit" : "myunit" }, { "var_id" : 32, "var_name" : "b", "abbrev" : "whatever2", "unit" : "myunit3" } ] } ] })
# result=t.meta.listCollectionNames(db='StreamsTACCDB')
# t.meta.listDocuments(db='StreamsTACCDB',collection='Proj1')
# result, debug = t.meta.listCollectionNames(db='StreamsTACCDB', _tapis_debug=True)

def list_sites(project_id):
    resp={}
    result = t.meta.listDocuments(db=conf.streamd_db,collection=project_id)
    str = result.decode('utf-8')
#    json_result = json.dumps(str)
    resp['results'] = json.loads(str)
    return resp

def get_site(project_id, site_id):
    return ""
