import enum
import requests
import json
from flask import g, Flask
from tapisservice.tapisflask.utils import conf
import datetime
app = Flask(__name__)

from common import utils, errors
from service import auth
from service import chords
# get the logger instance -
from tapisservice.logs import get_logger
logger = get_logger(__name__)


t = auth.t

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
    logger.debug('in META list project')
    result= t.meta.listDocuments(_tapis_set_x_headers_from_service=True, db=conf.tenant[g.tenant_id]['stream_db'],collection='streams_project_metadata',filter='{"permissions.users":"'+g.username+'","tapis_deleted":null}')
    logger.debug(result)
    if len(json.loads(result.decode('utf-8'))) > 0:
        message = "Projects found"
    else:
        raise errors.ResourceError(msg=f'No Projects found')
    logger.debug(result)
    return json.loads(result.decode('utf-8')), message

#TODO add project get
def get_project(project_id):
    logger.debug('In GET Project')
    result = t.meta.listDocuments(_tapis_set_x_headers_from_service=True, db=conf.tenant[g.tenant_id]['stream_db'],collection='streams_project_metadata', filter='{"project_id":"'+project_id+'","tapis_deleted":null}')
    logger.debug(result)
    logger.debug(len(result.decode('utf-8')))
    if len(json.loads(result.decode('utf-8'))) > 0:
        logger.debug('PROJECT FOUND')
        message = "Project found."
        proj_result = json.loads(result.decode('utf-8'))[0]
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
    col_result, col_bug =t.meta.createCollection(_tapis_set_x_headers_from_service=True, db=conf.tenant[g.tenant_id]['stream_db'],collection=req_body['project_id'], _tapis_debug=True)
    logger.debug(col_bug.response.status_code)
    if col_bug.response.status_code == 201:
        logger.debug('Created project metadata')
        #create project collection
        result, bug =t.meta.createDocument(_tapis_set_x_headers_from_service=True, db=conf.tenant[g.tenant_id]['stream_db'], collection='streams_project_metadata', request_body=req_body, _tapis_debug=True)
        logger.debug("Status_Code: " + str(bug.response.status_code))
        logger.debug(result)
        if str(bug.response.status_code) == '201':
            message = "Project Created"
            index_result, index_bug = t.meta.createIndex(_tapis_set_x_headers_from_service=True, db=conf.tenant[g.tenant_id]['stream_db'], collection=req_body['project_id'],indexName=body['project_id']+"_loc_index", request_body={"keys":{"location": "2dsphere"}}, _tapis_debug=True)
            #create location index
            logger.debug(index_result)
            results, bug= get_project(req_body['project_id'])

        else:
            #should remove project metadata record if this fails
            raise errors.ResourceError(msg=f'Project Creation Failed')
            results=bug.response
    else:
        logger.debug('Project id already exists')
        results = 'null'
        logger.debug(results)
        message='Project id already exists'
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
        result, put_bug =t.meta.replaceDocument(_tapis_set_x_headers_from_service=True, db=conf.tenant[g.tenant_id]['stream_db'], collection='streams_project_metadata', docId=proj_result['_id']['$oid'], request_body=proj_result, _tapis_debug=True)
        logger.debug(put_bug.response.status_code)
        if put_bug.response.status_code == 200:
            result = proj_result
            message = 'Project Updated'
    else:
        raise errors.ResourceError(msg=f'Project Does Not Exist For Project ID:'+str(project_id))
    return result, message

def delete_project(project_id):
    logger.debug("IN DELETE Project META")
    proj_result, proj_bug = get_project(project_id)
    if len(proj_result) > 0:
        proj_result['last_updated'] = str(datetime.datetime.now())
        proj_result['tapis_deleted'] = True
        #validate fields
        logger.debug(proj_result)
        result={}
        message=""
        result, put_bug =t.meta.replaceDocument(_tapis_set_x_headers_from_service=True, db=conf.tenant[g.tenant_id]['stream_db'], collection='streams_project_metadata', docId=proj_result['_id']['$oid'], request_body=proj_result, _tapis_debug=True)
        logger.debug(put_bug.response.status_code)
        if put_bug.response.status_code == 200:
            result = proj_result
            message = 'Project Deleted'
    else:
        raise errors.ResourceError(msg=f'Project Does Not Exist For Project ID:'+str(project_id))
    return result, message

#strip out id and _etag fields
def list_sites(project_id):
    result = t.meta.listDocuments(_tapis_set_x_headers_from_service=True, db=conf.tenant[g.tenant_id]['stream_db'],collection=project_id,filter='{"tapis_deleted":{ "$exists" : false },"site_id":{ "$exists" : true }}')
    if len(json.loads(result)) > 0:
        message = "Sites found"
    else:
        raise errors.ResourceError(msg='No Sites found')
    logger.debug(result)
    return json.loads(result.decode('utf-8')), message

#strip out id and _etag fields
def get_site(project_id, site_id):
    logger.debug('In GET Site')
    result = t.meta.listDocuments(_tapis_set_x_headers_from_service=True, db=conf.tenant[g.tenant_id]['stream_db'],collection=project_id,filter='{"$and":[{"site_id":"'+site_id+'"},{"tapis_deleted":{ "$exists" : false }}]}')
    if len(json.loads(result)) > 0:
        message = "Site found."
        #result should be an object not an array
        logger.debug(result)
        site_result = json.loads(result.decode('utf-8'))[0]
        result = site_result
        logger.debug("SITE FOUND")
    else:
        logger.debug("NO SITE FOUND")
        raise errors.ResourceError(msg='No Site Found Matching Site ID: '+site_id+' In Project: '+project_id)
        #result = ''
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
    result, bug =t.meta.createDocument(_tapis_set_x_headers_from_service=True, db=conf.tenant[g.tenant_id]['stream_db'], collection=project_id, request_body=req_body, _tapis_debug=True)
    logger.debug(bug.response.status_code)
    logger.debug(result)
    if bug.response.status_code == 201:
        message = "Site Created."
        #fetch site document to serve back
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
        if 'location' not in put_body:
            site_result['location'] = {"type":"Point", "coordinates":[float(put_body['longitude']),float(put_body['latitude'])]}
        site_result['last_updated'] = str(datetime.datetime.now())
        #validate fields
        logger.debug(site_result)
        result={}
        message=""
        result, put_bug =t.meta.replaceDocument(_tapis_set_x_headers_from_service=True, db=conf.tenant[g.tenant_id]['stream_db'], collection=project_id, docId=site_result['_id']['$oid'], request_body=site_result, _tapis_debug=True)
        logger.debug(put_bug.response.status_code)
        if put_bug.response.status_code == 200:
            result = site_result
            message = 'Site Updated'
    else:
        raise errors.ResourceError(msg=f'Site Does Not Exist For Site ID:'+str(site_id))
    return result, message


def delete_site(project_id, site_id):
    site_result, msg = get_site(project_id,site_id)
    site_result['tapis_deleted'] = True
    result, up_message = update_site(project_id, site_id, site_result)
    if up_message == 'Site Updated':
        message = 'Site Deleted'
    return {},message

def get_instrument(project_id, site_id, instrument_id):
    result = {}
    site_result, site_bug = get_site(project_id,site_id)
    if len(site_result) > 0:
        logger.debug("Site  FOUND")
        for inst in site_result['instruments']:
            logger.debug(inst)
            if 'tapis_deleted' not in inst:
                    #make sure this object has the inst_id key
                if 'inst_id' in inst:
                        #check id for match
                    if str(inst['inst_id']) == str(instrument_id):
                        logger.debug("INSTRUMENT FOUND")
                        if 'variables' in inst :
                            if len(inst['variables']) > 0:
                                logger.debug('In Variables')
                                cur_variables = []
                                for variable in inst['variables']:
                                    logger.debug(variable)
                                    if 'tapis_deleted' not in variable:
                                        cur_variables.append(variable)
                                inst['variables'] = cur_variables
                        result = inst
                        message = "Instrument Found"
        if len(result) == 0:
            message = "Instrument Not Found"
            raise errors.ResourceError(msg=f'Instrument Not Found With Instrument ID: '+instrument_id)
    else:
        message ="Site Not Found - Instrument Does Not Exist"
    return result, message

def get_instrument_by_id(inst_id):
    #get index
    result = fetch_instrument_index(inst_id)
    logger.debug(result)
    if len(result) > 0:
        #get updated_instruments
        inst_result, inst_msg = get_instrument(result['project_id'],result['site_id'],inst_id)
        return inst_result, inst_msg
    else:
        return {},"Instrument ID not found"

def list_instruments(project_id, site_id):
    site_result, site_bug = get_site(project_id,site_id)
    if len(site_result) > 0:
        instruments = []
        if 'instruments' in site_result:
            if len(site_result['instruments']) > 0:
                for inst in site_result['instruments']:
                    if 'tapis_deleted' not in inst:
                        instruments.append(inst)
                result = instruments
                message = "Instruments Found"
            else:
                result = {}
                message = "No Instruments Found"
                raise errors.ResourceError(msg=f'No Instruments Found for Site ID:' + str(site_id))
        else:
            result = {}
            message = "No Instruments Found"
            raise errors.ResourceError(msg=f'No Instruments Found for Site ID:'+str(site_id))
    else:
        result = {}
        message ="Site Not Found - No Instruments Exist"
        raise errors.ResourceError(msg=f'Site Not Found With Site ID:'+str(site_id))
    return result, message

def create_instrument(project_id, site_id, post_body):
    #check for existing instrument id
    logger.debug("In Create Instrument")
    inst_index_result = fetch_instrument_index(post_body['inst_id'])
    logger.debug(inst_index_result)
    logger.debug("AFTER FETCH INST")
    if len(inst_index_result) == 0 and 'instrument_id' not in inst_index_result:
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
            result, post_bug =t.meta.replaceDocument(_tapis_set_x_headers_from_service=True, db=conf.tenant[g.tenant_id]['stream_db'], collection=project_id, docId=site_result['_id']['$oid'], request_body=site_result, _tapis_debug=True)
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
    else:
        raise errors.ResourceError(msg=f'"Instrument ID already exists! A unique instrument ID across the Streams API must be used. Could not create Instrument"')
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
            logger.debug("A")
            if 'inst_id' in inst:
                if str(inst['inst_id']) == str(instrument_id):
                    logger.debug("INT ID MATCHES")
                    inst_exists=True;
                    if remove_instrument == False:
                        logger.debug("INT REM FALSE")
                        #add vars from current instrument so they are not removed
                        inst_body['inst_id'] = instrument_id
                        inst_body['chords_id'] = inst['chords_id']
                        if 'variables' in inst:
                            inst_body['variables'] = inst['variables']
                        updated_instruments.append(inst_body)
                    else:
                        #soft delete instrument
                        inst['tapis_deleted']=True
                        updated_instruments.append(inst)
                else:
                    updated_instruments.append(inst)
        if inst_exists:
            logger.debug("ADDING INSTRUMENTS TO SITE")
            site_result['instruments'] = updated_instruments
            logger.debug("UPDATE/DELETE INSTRUMENT")
            logger.debug(site_result)
            result, put_bug =t.meta.replaceDocument(_tapis_set_x_headers_from_service=True, db=conf.tenant[g.tenant_id]['stream_db'], collection=project_id, docId=site_result['_id']['$oid'], request_body=site_result, _tapis_debug=True)
            logger.debug(put_bug.response.status_code)
            if put_bug.response.status_code == 200:
                logger.debug("In RESPONSE block")
                inst_body['site_chords_id'] = site_result['chords_id']
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
    logger.debug(site_result)
    inst_exists = False
    result =[]
    if len(site_result) > 0:
        logger.debug('inside if')
        for inst in site_result['instruments']:
            if inst['inst_id'] == instrument_id:
                inst_exists = True
                if 'variables' in inst:
                    logger.debug('inside if variables')
                    variables =[]
                    for variable in inst['variables']:
                        logger.debug(variable)
                        if 'tapis_deleted' not in variable:
                            variables.append(variable)
                        logger.debug(result)
                    result = variables
                if len(result) > 0 :
                    message = "Variables Found"
                else:
                    message = "No Variables Found"
                    raise errors.ResourceError(msg=f'" No Variables Found for Site ID:'+str(site_id))
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
    logger.debug(message)
    result = {}
    if len(site_result) > 0:
        for inst in site_result['instruments']:
            if inst['inst_id'] == instrument_id:
                inst_exists = True
                if 'variables' in inst :
                    if len(inst['variables']) > 0:
                        logger.debug('In Variables')
                        for variable in inst['variables']:
                            logger.debug(variable)
                            if 'tapis_deleted' not in variable:
                                if 'var_id' in variable:
                                    if str(variable['var_id']) == str(variable_id):
                                        result = variable
                                        message = "Variable Found"
                                        logger.debug('Variable Found')
        if inst_exists == False:
            result = []
            message = "Instrument Not Found - No Variables Exist"
        logger.debug('end of if')
    else:
        message ="Site Not Found - Instrument Does Not Exist - No Variables Exist"
    logger.debug("END")
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
            result, put_bug =t.meta.replaceDocument(_tapis_set_x_headers_from_service=True, db=conf.tenant[g.tenant_id]['stream_db'], collection=project_id, docId=site_result['_id']['$oid'], request_body=site_result, _tapis_debug=True)
            logger.debug(put_bug.response.status_code)
            if put_bug.response.status_code == 200:
                result = var_body
                message = "Variable Created"
            else:
                res,mgs = chords.delete_variable(post_body['chords_id'])
                raise errors.ResourceError(msg=f'Variable Failed to be Created')
        else:
            raise errors.ResourceError(msg=f'Instrument Not Found For This Site. Variable Create Failed')
    else:
        raise errors.ResourceError(msg=f'Site Not Found - Cannote Create Variable')

    return result, message

#update and remove variable
def update_variable(project_id, site_id, instrument_id, variable_id, put_body, remove_variable=False):
    #fetch site document that should contain the instrument
    site_result, site_bug = get_site(project_id,site_id)
    #flag to track if the instrument exists in this site
    inst_exists = False;
    inst_body ={}
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
                if 'variables' in inst_body:
                    for variable in inst['variables']:
                        if 'var_id' in variable:
                            if variable['var_id'] == variable_id:
                                if remove_variable == False:
                                    #replace variable with new changes
                                    var_body['chords_id'] = variable['chords_id']
                                    logger.debug("SETTING CHORDS ID*****************************")
                                    updated_variables.append(var_body)
                                else:
                                    #soft delete variable
                                    variable['tapis_deleted'] =True;
                                    variable['updated_at']=str(datetime.datetime.now())
                                    updated_variables.append(variable)
                            else:
                                #keep variable
                                updated_variables.append(variable)
                        else:
                            #keep variable
                            updated_variables.append(variable)
                inst_body['variables']= updated_variables
                updated_instruments.append(inst_body)
            else:
                updated_instruments.append(inst)
        if inst_exists:
            site_result['instruments'] = updated_instruments
            logger.debug("UPDATE/DELETE VARIABLE")
            logger.debug(site_result)
            result, put_bug =t.meta.replaceDocument(_tapis_set_x_headers_from_service=True, db=conf.tenant[g.tenant_id]['stream_db'], collection=project_id, docId=site_result['_id']['$oid'], request_body=site_result, _tapis_debug=True)
            logger.debug(put_bug.response.status_code)
            if put_bug.response.status_code == 200:
                logger.debug(site_result)
                logger.debug(inst_body)
                #var_body['site_chords_id'] = site_result['chords_id']
                var_body['inst_chords_id'] = inst_body['chords_id']
                result = var_body
                logger.debug(result)
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
    result, bug =t.meta.createDocument(_tapis_set_x_headers_from_service=True, db=conf.tenant[g.tenant_id]['stream_db'], collection='streams_instrument_index', request_body=req_body, _tapis_debug=True)
    return result, str(bug.response.status_code)

def fetch_instrument_index(instrument_id):
    result= t.meta.listDocuments(_tapis_set_x_headers_from_service=True, db=conf.tenant[g.tenant_id]['stream_db'],collection='streams_instrument_index',filter='{"instrument_id":"'+instrument_id+'"}')
    json_res = json.loads(result.decode('utf-8'))
    if len(json_res) > 0:
        return json.loads(result.decode('utf-8'))[0]
    else:
        return json.loads(result.decode('utf-8'))

# create alert metadata
def create_alert(alert):
    alert_result,alert_bug = t.meta.createDocument(_tapis_set_x_headers_from_service=True, db=conf.tenant[g.tenant_id]['stream_db'], collection='streams_alerts_metadata', request_body=alert, _tapis_debug=True)
    if str(alert_bug.response.status_code) == '201':
        logger.debug(alert_bug.response)
        logger.debug(alert_result)
        # TODO strip out _id and _etag
        result, alert_get_bug = get_alert(alert['channel_id'], alert['alert_id'])
        message = "Alert Added"
    else:
        message = "Alert Failed to Create"
        result = ''
        logger.debug(message + " : Unable to connect to Tapis Meta Server: " + alert_bug)
    return result, message

#strip out id and _etag fields
def get_alert(channel_id,alert_id):
    logger.debug('In GET alert')
    result = t.meta.listDocuments(_tapis_set_x_headers_from_service=True, db=conf.tenant[g.tenant_id]['stream_db'],collection='streams_alerts_metadata',filter='{"alert_id":"'+ alert_id +'"}')
    if len(result.decode('utf-8')) > 0:
        message = "Alert found."
        #result should be an object not an array
        alert_result = json.loads(result.decode('utf-8'))[0]
        result = alert_result
        logger.debug("ALERT FOUND")
        return result, message
    else:
        logger.debug("NO ALERT FOUND")
        raise errors.ResourceError(msg=f'No Alert found: {alert_id}')


def list_alerts(channel_id):
    logger.debug("Before")
    result = t.meta.listDocuments(_tapis_set_x_headers_from_service=True, db=conf.tenant[g.tenant_id]['stream_db'],collection='streams_alerts_metadata',filter='{"channel_id":"'+ channel_id+'"}')
    logger.debug("After")
    if len(result) > 0 :
        message = "Alerts found"
        logger.debug(result)
        return json.loads(result.decode('utf-8')), message
    else:
        raise errors.ResourceError(msg=f'No Alert found')

def list_templates():
    logger.debug("Before")
    result = t.meta.listDocuments(_tapis_set_x_headers_from_service=True, db=conf.tenant[g.tenant_id]['stream_db'],collection='streams_templates_metadata',filter='{"permissions.users":"'+ g.username+'"}')
    logger.debug("After")
    if len(result) > 0 :
        message = "Templates found"
        logger.debug(result)
        return json.loads(result.decode('utf-8')), message
    else:
        raise errors.ResourceError(msg=f'No Template found')

#update template
def update_template(template):
    logger.debug('In META update_template')
    logger.debug('Channel: ' + template['template_id'] + ': ' + str(template['_id']['$oid']))
    result = {}
    result, put_bug = t.meta.replaceDocument(_tapis_set_x_headers_from_service=True, db=conf.tenant[g.tenant_id]['stream_db'], collection='streams_templates_metadata', docId=template['_id']['$oid'],
                                             request_body=template, _tapis_debug=True)
    logger.debug(put_bug.response)
    if put_bug.response.status_code == 200:
        result = template
        message = 'Template Updated'
    else:
        result = {}
        message = 'Could not update Template in meta'
        #TODO rollback the template change in the kapacitor template
    return result, message

#update channel
def update_channel(channel):
    logger.debug('In META update_channel')
    logger.debug('Channel: ' + channel['channel_id'] + ': ' + str(channel['_id']['$oid']))
    result = {}
    result, put_bug = t.meta.replaceDocument(_tapis_set_x_headers_from_service=True, db=conf.tenant[g.tenant_id]['stream_db'], collection='streams_channel_metadata', docId=channel['_id']['$oid'],
                                             request_body=channel, _tapis_debug=True)
    logger.debug(put_bug.response)
    if put_bug.response.status_code == 200:
        result = channel
        message = 'Channel Status Updated'
    else:
        result = {}
        message = 'Could not update Channel Status in meta'
        #TODO rollback the status change in the kapacitor task
    return result, message

def healthcheck():
    logger.debug('tenant arg')
    logger.debug(g.tenant_id)
    res = requests.get(conf.tenant[g.tenant_id]['tapis_base_url'] +'/v3/meta/healthcheck')
    return res.status_code
