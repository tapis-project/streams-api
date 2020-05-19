import requests
import json
import datetime
from flask import g, Flask
from common.config import conf
app = Flask(__name__)

from common import utils, errors
# get the logger instance -
from common.logs import get_logger
logger = get_logger(__name__)
import auth
from requests.auth import HTTPBasicAuth
import subprocess
import meta
#access the dynatpy instance
t = auth.t


#create a Kapacitor task and return the result content and status code
#Example body
#  body = {
#   "id" : "display",
#   "type" : "stream",
#   "dbrps": [{"db": "chords_ts_production", "rp" : "autogen"}],
#   "script": "stream\n |from()\n .measurement('tsdata')\n |httpOut('msg')\n",
#   "status": "enabled"
#   }
def create_task(body):
    #TODO - need to confirm task_id is unqiue probably
    logger.debug("IN CREATE TASK")
    headers = {
        'content-type': "application/json"
    }
    res = requests.post(conf.kapacitor_url+'/kapacitor/v1/tasks', json=body, headers=headers,auth=HTTPBasicAuth(conf.kapacitor_username, conf.kapacitor_password), verify=False)
    logger.debug('Kapacitor Response' + str(res.content))
    logger.debug('status_code'+ str(res.status_code))
    return json.loads(res.content),res.status_code

#list kapacitor tasks - probably will won't use much without adding query params
def list_tasks():
    headers = {
        'content-type': "application/json"
    }
    res = requests.get(conf.kapacitor_url+'/kapacitor/v1/tasks',auth=HTTPBasicAuth(conf.kapacitor_username, conf.kapacitor_password),  verify=False)
    return json.loads(res.content),res.status_code

def get_task(task_id):
    headers = {
        'content-type': "application/json"
    }
    res = requests.get(conf.kapacitor_url+'/kapacitor/v1/tasks'+task_id,auth=HTTPBasicAuth(conf.kapacitor_username, conf.kapacitor_password), verify=False)
    return json.loads(res.content),res.status_code

# enable/disable a task
def change_task_status(task_id,body):
    logger.debug("CHANGING TASK STATUS")
    logger.debug(conf.kapacitor_url + '/kapacitor/v1/tasks/' + task_id)
    logger.debug(body)
    headers = {
        'content-type': "application/json"
    }
    logger.debug(headers)
    try:
        res = requests.patch(conf.kapacitor_url + '/kapacitor/v1/tasks/' + task_id, headers=headers, json=body,
                       auth=HTTPBasicAuth(conf.kapacitor_username, conf.kapacitor_password), verify=False)
    except Exception as e:
        msg = f" Kapacitor bad request ; exception: {e}"
        raise errors.ResourceError(msg=msg)
    logger.debug('Kapacitor Response' + str(res.content))
    logger.debug('status_code' + str(res.status_code))
    return json.loads(res.content), res.status_code



####################### CHANNEL ########################################
# script field in req_body is temporary until we have use a template
#Expected values for req_body:
#  channel_id, channel_name, triggers_with_actions, task_id, status, created, last_updated, template_id
def create_channel(req_body):
    logger.debug("IN CREATE CHANNEL")
    #create a kapacitor task
    #task_body ={'id':req_body['task_id'], 'type':'stream','dbrps': [{"db": "chords_ts_production", "rp" : "autogen"}],'status':'enabled'}
    task_body = {'id': req_body['task_id'],
                 'dbrps': [{"db": "chords_ts_production", "rp": "autogen"}], 'status': 'enabled'}
    #TODO figure out how to make this - for now pass in a script for testing
    #task_body['script']=req_body['script']
    #task_body['triggers_with_actions'] = req_body['triggers_with_actions']
    task_body['template-id'] = req_body['template_id']
    task_body['vars'] = req_body['vars']
    task_body['vars']["channel_id"] = {"type": "string", "value": req_body['channel_id']}
    ktask_result, ktask_status = create_task(task_body)
    logger.debug(ktask_status)
    req_body['permissions']={'users':[g.username]}
    if ktask_status == 200:
        req_body['create_time'] = str(datetime.datetime.utcnow())
        #create a metadata record with kapacitor task id to the channel metadata collection
        mchannel_result, mchannel_bug =t.meta.createDocument(db=conf.stream_db, collection='streams_channel_metadata', request_body=req_body, _tapis_debug=True)
        logger.debug("Status_Code: " + str(mchannel_bug.response.status_code))
        logger.debug(mchannel_result)
        if str(mchannel_bug.response.status_code) == '201':
            message = "Channel Created"
            #get the newly created channel object to return
            result, bug= get_channel(req_body['channel_id'])
            logger.debug(result)
        else:
            #TODO need to remove task from kapacitor if this failed
            raise errors.ResourceError(msg=f'Channel Creation Failed')
            result=mchannel_bug.response
            message = "Channel Creation Failed"
    else:
        raise errors.ResourceError(msg=f'Channel Creation Failed')
        result=ktask_result
        message = "Channel Creation Failed"
    return result, message

def list_channels():
    logger.debug('in Channel list ')
    result= t.meta.listDocuments(db=conf.stream_db,collection='streams_channel_metadata',filter='{"permissions.users":"'+g.username+'"}')
    logger.debug(result)
    if len(result.decode('utf-8')) > 0:
        message = "Channels found"
    else:
        raise errors.ResourceError(msg=f'No Channels found')
    logger.debug(result)
    return json.loads(result.decode('utf-8')), message

def get_channel(channel_id):
    logger.debug('In GET Channel')
    result = t.meta.listDocuments(db=conf.stream_db,collection='streams_channel_metadata',filter='{"channel_id":"'+channel_id+'"}')
    if len(result.decode('utf-8')) > 0:
        message = "Channel found."
        channel_result = json.loads(result.decode('utf-8'))[0]
        result = channel_result
        logger.debug("CHANNEL FOUND")
    else:
        logger.debug("NO CHANNEL FOUND")
        raise errors.ResourceError(msg=f'No Channel found')
    return result, message

def update_channel():
    return True

def update_channel_status(channel_id, body):
    logger.debug('In update_channel_status')
    try:
        channel_result, msg = get_channel(channel_id)
    except Exception as e:
        msg = f" Channel {channel_id} NOT Found; exception: {e}"
        raise errors.ResourceError(msg=msg)

    logger.debug('UPDATING ... Kapacitor task')

    try:
        result,status_code = change_task_status(channel_result['task_id'],body)
    except Exception as e:
        msg = f" Not able to connect to Kapacitor for the task {channel_result['task_id']} status update; exception: {e}"
        raise errors.ResourceError(msg=msg)

    if status_code == 200:
        logger.debug("UPDATED ... Kapacitor task status ")
        logger.debug("UPDATING ... channel object in meta")
        logger.debug('status: ' + body['status'])
        if result['status']=='enabled':
            channel_result['status'] = 'ACTIVE'
        elif result['status']=='disabled':
            channel_result['status'] = 'INACTIVE'
        else:
            channel_result['status'] = 'ERROR'
        result = {}
        result, message = meta.update_channel(channel_result)
    else:
        msg = f" Could Not Find Channel {channel_id} with Task {channel_result['task_id']} "
        raise errors.ResourceError(msg=msg)
    return result,message

def remove_channel():
    return True

################### ALERT ############################################
def create_alert():
    return True

def get_alert():
    return True

def list_alerts():
    return True

# We are not going to allow update alert and remove_alert
#def update_alert():
#    return True

#def remove_alert():
 #   return True

################### TEMPLATE ##########################################

#create templates
def create_template(body):
    logger.debug("IN CREATE TEMPLATE")
    headers = {
        'content-type': "application/json"
    }
    json_req = {}
    json_req['id'] = body['template_id']
    json_req['type'] = 'stream'
    json_req['script'] = body['script']

    res = requests.post(conf.kapacitor_url + '/kapacitor/v1/templates', json=json_req, headers=headers, auth=HTTPBasicAuth(conf.kapacitor_username, conf.kapacitor_password), verify=False)
    logger.debug(res.content)
    logger.debug(res.status_code)
    #json.loads(res.content), res.status_code
    if res.status_code == 200:
        body['create_time'] = str(datetime.datetime.utcnow())
        #create a metadata record with kapacitor template id in the templates metadata collection
        #col_result, col_bug = t.meta.createCollection(db=conf.stream_db, collection='streams_templates_metadata',
        #                                             _tapis_debug=True)
        #if col_bug.response.status_code == 201:
         #  logger.debug('Created streams_templates_metadata')

        mtemplate_result, mtemplate_bug =t.meta.createDocument(db=conf.stream_db, collection='streams_templates_metadata', request_body=body, _tapis_debug=True)
        logger.debug("Status_Code: " + str(mtemplate_bug.response.status_code))
        logger.debug(mtemplate_result)
        if str(mtemplate_bug.response.status_code) == '201':
            message = "Template Created"
            #get the newly created channel object to return
            result, bug = get_template(body['template_id'])
            logger.debug(result)
        else:
            message = f'Template Creation in Meta Failed'
            #TODO Rollback- delete template in Kapacitor
            raise errors.ResourceError(msg=message)
    else:
        message = f'Kapacitor Template Creation Failed'
        raise errors.ResourceError(msg=message)

    return result, message

# get template
def get_template(template_id):
    logger.debug('In get_template ')
    result = t.meta.listDocuments(db=conf.stream_db, collection='streams_templates_metadata',
                                  filter='{"template_id":"' + template_id + '"}')
    if len(result.decode('utf-8')) > 0:
        message = "Template found."
        channel_result = json.loads(result.decode('utf-8'))[0]
        result = channel_result
        logger.debug("TEMPLATE FOUND")
    else:
        logger.debug("NO TEMPLATE FOUND")
        raise errors.ResourceError(msg=f'No TEMPLATE found')
    return result, message




#create templates
#TODO
def create_template_cli(template_id,path_template_file):
    logger.debug("IN CREATE TEMPLATE CLI")
    #kapacitor define-template <TEMPLATE_ID> -tick <PATH_TO_TICKSCRIPT> -type <stream|batch>
    output=subprocess.check_output(["kapacitor","define-template",template_id,"-tick",path_template_file,"-type","stream"],universal_newlines=True, check=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if output.returncode == 0 :
        return "template created"
    else:
        return "template not created"

#list templates
def list_templates():
    logger.debug("IN LIST TEMPLATES")
    headers={'content_type': 'application/json'}
    res = requests.get(conf.kapacitor_url + '/kapacitor/v1/templates', auth=HTTPBasicAuth(conf.kapacitor_username, conf.kapacitor_password), verify=False )
    return json.loads(res.content),res.status_code

#get a template
def get_template_kapacitor(template_id):
    logger.debug("IN GET TEMPLATE")
    headers={'content_type': 'application/json'}
    res = requests.get(conf.kapacitor_url + '/kapacitor/v1/templates' + template_id, auth=HTTPBasicAuth(conf.kapacitor_username, conf.kapacitor_password), verify=False)
    return json.loads(res.content),res.status_code

def update_template():
    return True

def remove_template():
    return True

############################ CHANNEL INDEX #############################
def create_channel_index(project_id, channel_id):
    req_body = {'project_id':project_id, 'channel_id': channel_id}
    result, bug =t.meta.createDocument(db=conf.stream_db, collection='streams_channel_index', request_body=req_body, _tapis_debug=True)
    return result, str(bug.response.status_code)

def fetch_channel_index(channel_id):
    result= t.meta.listDocuments(db=conf.stream_db,collection='streams_channel_index',filter='{"channel_id":"'+channel_id+'"}')
    return json.loads(result.decode('utf-8'))
