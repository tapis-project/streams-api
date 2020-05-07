import enum
import requests
import json
from flask import g, Flask
from common.config import conf
from common import auth
import datetime
app = Flask(__name__)

from common import utils, errors
from tapy.dyna import DynaTapy
import auth
# get the logger instance -
from common.logs import get_logger
logger = get_logger(__name__)

#pull out tenant from JWT
# t = DynaTapy(base_url=conf.tapis_base_url, username=conf.streams_user, service_password=conf.service_password, account_type=conf.streams_account_type, tenant_id='master')
# t.get_tokens()
t = auth.t
# result=t.meta.createDocument(db='StreamsTACCDB', collection='Proj1', request_body={ "site_id" : 1234299, "lat" : 70.5, "lon" : 90, "instruments" : [ { "inst_id" : 2334, "inst_name" : "myinstrument", "variables" : [ { "var_id" : 34, "var_name" : "a", "abbrev" : "whatever", "unit" : "myunit" } ] }, { "inst_id" : 2435, "inst_name" : "myinstrument2","variables" : [ { "var_id" : 33, "var_name" : "a", "abbrev" : "whatever", "unit" : "myunit" }, { "var_id" : 32, "var_name" : "b", "abbrev" : "whatever2", "unit" : "myunit3" } ] } ] })
# result=t.meta.listCollectionNames(db='StreamsTACCDB')
# t.meta.listDocuments(db='StreamsTACCDB',collection='Proj1')
# result, debug = t.meta.listCollectionNames(db='StreamsTACCDB', _tapis_debug=True)


#strip off the _id and _etag from metadata objects
def strip_meta(meta_object):
    meta_object.pop('_id')
    meta_object.pop('_etag')
    return meta_object

#strip off the _id and _etag for a list of metadata objects
def strip_meta_list(meta_list):
    new_list = []
    for item in meta_list:
        new_list.append(strip_meta(item))
    return new_list

#List projects a user has permission to read
#strip out id and _etag fields
def list_projects():
    #get user role with permission ?
    logger.debug('in META list project')
    result= t.meta.listDocuments(db=conf.stream_db,collection='streams_project_metadata',filter='{"permissions.users":"'+g.username+'"}')
    logger.debug(result)
    if len(result.decode('utf-8')) > 0:
        message = "Projects found"
    else:
        raise errors.ResourceError(msg=f'No Projects found')
    logger.debug(result)
    return json.loads(result.decode('utf-8')), message

#TODO add project get
def get_project(project_id):
    logger.debug('In GET Project')
    result = t.meta.listDocuments(db=conf.stream_db,collection='streams_project_metadata',filter='{"project_id":"'+project_id+'"}')
    logger.debug(result)
    if len(result.decode('utf-8')) > 0:
        logger.debug('PROJECT FOUND')
        message = "Project found."
        proj_result = json.loads(result.decode('utf-8'))[0]
        #proj_result.pop('_id')
        #proj_result.pop('_etag')
        result = proj_result
    else:
        logger.debug("NO PROJECT FOUND")
        raise errors.ResourceError(msg=f'No Project found')
        result = ''
    return result, message

#TODO delete project metadata document if collection creation fails
def create_project(body):
    logger.debug("IN CREATE PROJECT META")
    results=''
    #create project metadata record
    req_body = body
    req_body['project_id'] = body['project_name'].replace(" ", "")
    req_body['permissions']={'users':[g.username]}
    logger.debug(req_body)
    #Check if project_id exists by creating collection - if so add something to id to unique it.
    col_result, col_bug =t.meta.createCollection(db=conf.stream_db,collection=req_body['project_id'], _tapis_debug=True)
    if col_bug.response.status_code == 201:
        logger.debug('Created project metadata')
        #create project collection
        result, bug =t.meta.createDocument(db=conf.stream_db, collection='streams_project_metadata', request_body=req_body, _tapis_debug=True)
        logger.debug("Status_Code: " + str(bug.response.status_code))
        logger.debug(result)
        if str(bug.response.status_code) == '201':
            message = "Project Created"
            index_result, index_bug = t.meta.createIndex(db=conf.stream_db, collection=req_body['project_id'],indexName=body['project_id']+"_loc_index", request_body={"keys":{"location": "2dsphere"}}, _tapis_debug=True)
            #create location index
            logger.debug(index_result)
            results, bug= get_project(req_body['project_id'])

        else:
            #should remove project metadata record if this fails
            raise errors.ResourceError(msg=f'Project Creation Failed')
            results=bug.response
    else:
        raise errors.ResourceError(msg=f'Project Creation Failed')
        results =bug.response
    return results, message

def update_project(project_id, put_body):
    logger.debug("IN Update Project META")
    proj_result, proj_bug = get_project(project_id)
    if len(proj_result) > 0:
        for field in put_body:
            proj_result[field] = put_body[field]
        proj_result['last_updated'] = str(datetime.datetime.now())
        #validate fields
        logger.debug(proj_result)
        result={}
        message=""
        result, put_bug =t.meta.replaceDocument(db=conf.stream_db, collection='streams_project_metadata', docId=proj_result['_id']['$oid'], request_body=proj_result, _tapis_debug=True)
        logger.debug(put_bug.response.status_code)
        if put_bug.response.status_code == 200:
            result = proj_result
            message = 'Project Updated'
    else:
        raise errors.ResourceError(msg=f'Project Does Not Exist For Project ID:'+str(project_id))
    return result, message

#strip out id and _etag fields
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

#strip out id and _etag fields
def get_site(project_id, site_id):
    logger.debug('In GET Site')
    result = t.meta.listDocuments(db=conf.stream_db,collection=project_id,filter='{"site_id":"'+site_id+'"}')
    if len(result.decode('utf-8')) > 0:
        message = "Site found."
        #result should be an object not an array
        #TODO strip out _id and _etag
        site_result = json.loads(result.decode('utf-8'))[0]
        #site_result.pop('_id')
        #site_result.pop('_etag')
        result = site_result
        logger.debug("SITE FOUND")
    else:
        logger.debug("NO SITE FOUND")
        raise errors.ResourceError(msg=f'No Site found')
        result = ''
    return result, message

#TODO need to validate required fields and GEOJSON field
def create_site(project_id, chords_site_id, body):
    logger.debug("IN CREATE SITE META")
    resp={}
    req_body = body
    req_body['chords_id'] = chords_site_id
    req_body['created_at'] = str(datetime.datetime.now())
    req_body['location'] = {"type":"Point", "coordinates":[float(req_body['longitude']),float(req_body['latitude'])]}
    #TODO validate fields
    logger.debug(body)
    result, bug =t.meta.createDocument(db=conf.stream_db, collection=project_id, request_body=req_body, _tapis_debug=True)
    logger.debug(bug.response.status_code)
    logger.debug(result)
    if bug.response.status_code == 201:
        message = "Site Created."
        #fetch site document to serve back
        #TODO strip out _id and _etag
        result, site_bug = get_site(project_id, str(req_body['site_id']))
    else:
        #remove site from Chords
        message = "Site Failed to Create."
        result = ''
    logger.debug(message)
    return result, message

#TODO validate field
#DO WE STRIP OUT Instruments field from put_body?
def update_site(project_id, site_id, put_body):
    logger.debug("IN Update SITE META")
    #fetch site first and then replace existing fields/add fields to current site document
    site_result, site_bug = get_site(project_id, site_id)
    if len(site_result) > 0:
        for field in put_body:
            site_result[field] = put_body[field]
        site_result['last_updated'] = str(datetime.datetime.now())
        #validate fields
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

def get_instrument(project_id, site_id, instrument_id):
    result = {}
    site_result, site_bug = get_site(project_id,site_id)
    if len(site_result) > 0:
        logger.debug("Site  FOUND")
        for inst in site_result['instruments']:
            logger.debug(inst)
            #make sure this object has the inst_id key
            if 'inst_id' in inst:
                #check id for match
                if str(inst['inst_id']) == str(instrument_id):
                    logger.debug("INSTRUMENT FOUND")
                    result = inst
                    message = "Instrument Found"
        if len(result) == 0:
            message = "Instrument Not Found"
    else:
        message ="Site Not Found - Instrument Does Not Exist"
    return result, message

def list_instruments(project_id, site_id):
    site_result, site_bug = get_site(project_id,site_id)
    if len(site_result) > 0:
        result = site_result['instruments']
        message = "Instruments Found"
    else:
        message ="Site Not Found - No Instruments Exist"
    return result, message

def create_instrument(project_id, site_id, post_body):
    site_result, site_bug = get_site(project_id,site_id)
    result ={}
    logger.debug(site_result)
    logger.debug(len(site_result))
    if len(site_result) > 0:
        inst_body = post_body
        inst_body['created_at'] = str(datetime.datetime.now())
        if 'instruments' in site_result:
            site_result['instruments'].append(inst_body)
        else:
            site_result['instruments'] = [inst_body]
        logger.debug("ADD INSTRUMENT")
        logger.debug(site_result)
        result, post_bug =t.meta.replaceDocument(db=conf.stream_db, collection=project_id, docId=site_result['_id']['$oid'], request_body=site_result, _tapis_debug=True)
        logger.debug(post_bug.response.status_code)
        if post_bug.response.status_code == 200:
            result = inst_body
            message = "Instrument Created"
            index_result = create_instrument_index(project_id, site_id, inst_body['inst_id'], inst_body['chords_id'])
            logger.debug(index_result)
        else:
            message = "Instrument Failed to Create"
    else:
        message ="Site Not Found - Cannote Create Instrument"
    return result, message

#This can update an instrument or remove it
def update_instrument(project_id, site_id, instrument_id, put_body, remove_instrument=False):
    logger.debug("IN UPDATE INSTRUMENT ID:" + instrument_id)
    #fetch site document that should contain the instrument
    site_result, site_bug = get_site(project_id,site_id)
    #flag to track if the instrument exists in this site
    logger.debug(site_result)
    logger.debug(len(site_result))
    inst_exists = False;
    result = {}
    if len(site_result) > 0:
        logger.debug("IN IF")
        inst_body = put_body
        inst_body['updated_at'] = str(datetime.datetime.now())
        updated_instruments = []
        for inst in site_result['instruments']:
            logger.debug("IN LOOP")
            if 'instrument_id' in inst:
                if str(inst['instrument_id']) == str(instrument_id):
                    logger.debug("INT ID MATCHES")
                    inst_exists=True;
                    if remove_instrument == False:
                        logger.debug("INT REM FALSE")
                        #add vars from current instrument so they are not removed
                        inst_body['instrument_id'] = instrument_id
                        inst_body['chords_id'] = inst['chords_id']
                        if 'variables' in inst:
                            inst_body['variables'] = inst['variables']
                        updated_instruments.append(inst_body)
                else:
                    updated_instruments.append(inst)
        if inst_exists:
            logger.debug("ADDING INSTRUMENTS TO SITE")
            site_result['instruments'] = updated_instruments
            logger.debug("UPDATE/DELETE INSTRUMENT")
            logger.debug(site_result)
            result, put_bug =t.meta.replaceDocument(db=conf.stream_db, collection=project_id, docId=site_result['_id']['$oid'], request_body=site_result, _tapis_debug=True)
            logger.debug(put_bug.response.status_code)
            if put_bug.response.status_code == 200:
                result = inst_body
                if remove_instrument:
                    message = "Instrument Deleted"
                else:
                    message = "Instrument updated"
            else:
                if remove_instrument:
                    message = "Instrument Failed to Delete"
                else:
                    message = "Instrument Failed to Update"
        else:
            if remove_instrument:
                message = "Instrument Not Found For This Site. Delete Failed"
            else:
                message = "Instrument Not Found For This Site. Update Failed"
    else:
        message ="Site Not Found - Cannote Create Instrument"
    return result, message


def list_variables(project_id, site_id, instrument_id):
    site_result, site_bug = get_site(project_id,site_id)
    inst_exists = False
    result =[]
    if len(site_result) > 0:
        for inst in site_result['instruments']:
            if inst['inst_id'] == instrument_id:
                inst_exists = True
                result = inst['variables']
                message = "Variables Found"
        if inst_exists == False:
            result = []
            message = "Instrument Not Found - No Variables Exist"
    else:
        message ="Site Not Found - Instrument Does Not Exist - No Variables Exist"
    return result, message

def get_variable(project_id, site_id, instrument_id, variable_id):
    site_result, site_bug = get_site(project_id,site_id)
    inst_exists = False
    message = "No Variable with variable_id: "+str(variable_id)+" Found"
    result = {}
    if len(site_result) > 0:
        for inst in site_result['instruments']:
            if inst['inst_id'] == instrument_id:
                inst_exists = True
                if 'variables' in inst:
                    for variable in inst['variables']:
                        if str(variable['var_id']) == str(var_id):
                            result = variable
                            message = "Variable Found"
        if inst_exists == False:
            result = []
            message = "Instrument Not Found - No Variables Exist"
    else:
        message ="Site Not Found - Instrument Does Not Exist - No Variables Exist"
    return result, message

def create_variable(project_id, site_id, instrument_id, post_body):
    #fetch site document that should contain the instrument
    site_result, site_bug = get_site(project_id,site_id)
    #flag to track if the instrument exists in this site
    inst_exists = False;
    result={}
    if len(site_result) > 0:
        var_body = post_body
        var_body['updated_at'] = str(datetime.datetime.now())
        updated_instruments = []
        for inst in site_result['instruments']:
            if 'inst_id' in inst:
                if inst['inst_id'] == instrument_id:
                    inst_exists=True;
                    inst_body = inst
                    #add variable to current instrument
                    if 'variables' in inst_body:
                        inst_body['variables'].append(var_body)
                    else:
                        inst_body['variables'] = [var_body]
                    updated_instruments.append(inst_body)
                else:
                    updated_instruments.append(inst)
        if inst_exists:
            site_result['instruments'] = updated_instruments
            logger.debug("ADD VARIABLE")
            logger.debug(site_result)
            result, put_bug =t.meta.replaceDocument(db=conf.stream_db, collection=project_id, docId=site_result['_id']['$oid'], request_body=site_result, _tapis_debug=True)
            logger.debug(put_bug.response.status_code)
            if put_bug.response.status_code == 200:
                result = var_body
                message = "Variable Created"
            else:
                message = "Variable Failed to be Created"
        else:
            message = "Instrument Not Found For This Site. Variable Create Failed"
    else:
        message ="Site Not Found - Cannote Create Variable"
    return result, message

#update and remove variable
def update_variable(project_id, site_id, instrument_id, variable_id, put_body, remove_variable=False):
    #fetch site document that should contain the instrument
    site_result, site_bug = get_site(project_id,site_id)
    #flag to track if the instrument exists in this site
    inst_exists = False;
    result={}
    if len(site_result) > 0:
        var_body = put_body
        var_body['var_id'] = variable_id
        var_body['updated_at'] = str(datetime.datetime.now())
        updated_variables = []
        updated_instruments = []
        for inst in site_result['instruments']:
            if inst['inst_id'] == instrument_id:
                inst_exists=True;
                inst_body = inst
                #add variable to current instrument
                if 'variable' in inst_body:
                    for variable in inst['variables']:
                        if variable['var_id'] == variable_id:
                            if remove_variable == False:
                                #replace variable with new changes
                                updated_variables.append(var_body)
                        else:
                            #keep variable
                            updated_variables.append(variable)
                inst_body['variables'].append(updated_variables)
                updated_instruments.append(inst_body)
            else:
                updated_instruments.append(inst)
        if inst_exists:
            site_result['instruments'] = updated_instruments
            logger.debug("UPDATE/DELETE VARIABLE")
            logger.debug(site_result)
            result, put_bug =t.meta.replaceDocument(db=conf.stream_db, collection=project_id, docId=site_result['_id']['$oid'], request_body=site_result, _tapis_debug=True)
            logger.debug(put_bug.response.status_code)
            if put_bug.response.status_code == 200:
                result = var_body
                if remove_variable == False:
                    message = "Variable Updated"
                else:
                    message = "Variable Deleted"
            else:
                if remove_variable == False:
                    message = "Variable Failed to be Updated"
                else:
                    message = "Variable Failed to be Deleted"
        else:
            if remove_variable == False:
                message = "Instrument Not Found For This Site. Variable Update Failed"
            else:
                message = "Instrument Not Found For This Site. Variable Delete Failed"
    else:
        if remove_variable == False:
            message ="Site Not Found - Cannote Create Variable"
        else:
            message = "Site Not Found - Cannote Delete Variable"
    return result, message

def create_instrument_index(project_id, site_id, instrument_id, chords_inst_id):
    req_body = {'project_id':project_id, 'site_id': site_id, 'instrument_id': instrument_id, 'chords_inst_id':chords_inst_id}
    result, bug =t.meta.createDocument(db=conf.stream_db, collection='streams_instrument_index', request_body=req_body, _tapis_debug=True)
    return result, str(bug.response.status_code)

def fetch_instrument_index(instrument_id):
    result= t.meta.listDocuments(db=conf.stream_db,collection='streams_instrument_index',filter='{"instrument_id":"'+instrument_id+'"}')
    return json.loads(result.decode('utf-8'))
