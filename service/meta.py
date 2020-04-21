import enum
import requests
import json
from flask import g, Flask
from common.config import conf
import datetime
app = Flask(__name__)

from common import utils, errors
from tapy.dyna import DynaTapy
# get the logger instance -
from common.logs import get_logger
logger = get_logger(__name__)

#pull out tenant from JWT
t = DynaTapy(base_url=conf.tapis_base_url, username=conf.streams_user, account_type=conf.streams_account_type, tenant_id=conf.tapis_tenant)
t.get_tokens()

# result=t.meta.createDocument(db='StreamsTACCDB', collection='Proj1', request_body={ "site_id" : 1234299, "lat" : 70.5, "lon" : 90, "instruments" : [ { "inst_id" : 2334, "inst_name" : "myinstrument", "variables" : [ { "var_id" : 34, "var_name" : "a", "abbrev" : "whatever", "unit" : "myunit" } ] }, { "inst_id" : 2435, "inst_name" : "myinstrument2","variables" : [ { "var_id" : 33, "var_name" : "a", "abbrev" : "whatever", "unit" : "myunit" }, { "var_id" : 32, "var_name" : "b", "abbrev" : "whatever2", "unit" : "myunit3" } ] } ] })
# result=t.meta.listCollectionNames(db='StreamsTACCDB')
# t.meta.listDocuments(db='StreamsTACCDB',collection='Proj1')
# result, debug = t.meta.listCollectionNames(db='StreamsTACCDB', _tapis_debug=True)

#List projects a user has permission to read
def list_projects():
    #get user role with permission ?
    result= t.meta.listDocuments(db='StreamsTACCDB',collection='streams_project_metadata',filter='{"permissions.users":"'+g.username+'"}')
    logger.debug(result)
    if len(result.decode('utf-8')) > 0:
        message = "Projects found"
    else:
        raise errors.ResourceError(msg=f'No Projects found')
    logger.debug(result)
    return json.loads(result.decode('utf-8')), message

#TODO delete project metadata document if collection creation fails
def create_project(body):
    logger.debug("IN CREATE PROJECT META")
    results=''
    #create project metadata record
    req_body = body
    req_body['project_id'] = body['project_name'].replace(" ", "")
    req_body['permissions']={'users':[g.username]}
    #Check if project_id exists - if so add something to id to unique it.
    result, bug =t.meta.createDocument(db=conf.stream_db, collection='streams_project_metadata', request_body=req_body, _tapis_debug=True)
    if bug.response.status_code == 201:
        logger.debug('Created project metadata')
        #create project collection
        col_result, col_bug =t.meta.createCollection(db=conf.stream_db,collection=body['project_id'], _tapis_debug=True)
        logger.debug(col_bug.response.status_code)
        logger.debug(col_result)
        if col_bug.response.status_code == 201:
            message = "Project Created"
            results=''
        else:
            #should remove project metadata record if this fails
            raise errors.ResourceError(msg=f'Project Creation Failed')
            results=bug.response
    else:
        raise errors.ResourceError(msg=f'Project Creation Failed')
        results =bug.response
    return results, message

def list_sites(project_id):
    logger.debug("Before")
    result = t.meta.listDocuments(db='StreamsTACCDB',collection=project_id)
    logger.debug("After")
    if len(result) > 0 :
        message = "Sites found"
    else:
        raise errors.ResourceError(msg=f'No Site found')
    logger.debug(result)
    return json.loads(result.decode('utf-8')), message

def get_site(project_id, site_id):
    logger.debug('In GET Site')
    result = t.meta.listDocuments(db=conf.stream_db,collection=project_id,filter='{"site_id":'+str(site_id)+'}')
    if len(result.decode('utf-8')) > 0:
        message = "Site found."
        result = json.loads(result.decode('utf-8'))[0]
    else:
        raise errors.ResourceError(msg=f'No Site found')
        result = ''
    return result, message

#TODO need to validate required fields and GEOJSON field
def create_site(project_id, site_id, body):
    logger.debug("IN CREATE SITE META")
    resp={}
    req_body = body
    req_body['site_id'] = site_id
    req_body['created_at'] = str(datetime.datetime.now())
    #TODO validate fields
    result, bug =t.meta.createDocument(db=conf.stream_db, collection=project_id, request_body=req_body, _tapis_debug=True)
    logger.debug(bug.response.status_code)
    logger.debug(result)
    if bug.response.status_code == 201:
        message = "Site Created."
        #fetch site document to serve back
        result, site_bug = get_site(project_id, site_id)
    else:
        #remove site from Chords
        message = "Site Failed to Create."
        result = ''
    logger.debug(message)
    return result, message

def update_site(project_id, site_id, put_body):
    logger.debug("IN Update SITE META")
    #fetch site first and then replace existing fields/add fields to current site document
    site_result, site_bug = get_site(project_id, site_id)
    if len(site_result) > 0:
        for field in put_body:
            site_result[field] = put_body[field]
        site_result['last_updated'] = str(datetime.datetime.now())
        logger.debug(site_result)
        result={}
        message=""
        result, put_bug =t.meta.replaceDocument(db=conf.stream_db, collection=project_id, docId=site_result['_id']['$oid'], request_body=site_result, _tapis_debug=True)
        logger.debug(put_bug.response.status_code)
        if put_bug.response.status_code == 200:
            result = site_result
            message = 'Site Updated'
    else:
        raise errors.ResourceError(msg=f'Site Does Not Exist For Site ID:'+str(site_id))
    return result, message


def delete_site(project_id, site_id):
    return ""
