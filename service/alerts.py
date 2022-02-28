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
from service import auth
from requests.auth import HTTPBasicAuth
import subprocess
from service import meta
from service import parse_condition_expr
from service import checks

# access the tapipy instance
t = auth.t


def create_task(body):
    #task_id is unqiue always
    logger.debug("IN CREATE TASK")
    headers = {
        'content-type': "application/json"
    }
    res = requests.post(conf.kapacitor_url+'/kapacitor/v1/tasks', json=body, headers=headers,auth=HTTPBasicAuth(conf.kapacitor_username, conf.kapacitor_password), verify=False)
    logger.debug('Kapacitor Response' + str(res.content))
    logger.debug('status_code'+ str(res.status_code))
    return json.loads(res.content),res.status_code

# list kapacitor tasks - probably will won't use much without adding query params
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

def ping():
    headers = {
        'content-type': "application/json"
    }
    res = requests.get(conf.kapacitor_url+'/kapacitor/v1/ping',auth=HTTPBasicAuth(conf.kapacitor_username, conf.kapacitor_password),  verify=False)
    return res.status_code



# enable/disable a task
def change_task_status(task_id, body):
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
    logger.debug('Kapacitor Response ' + str(res.content))
    logger.debug('status_code ' + str(res.status_code))
    return json.loads(res.content), res.status_code

# update a task
def update_kapacitor_task(task_id,body):
    logger.debug("UPDATING TASK ")
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
# Expected values for req_body:
#  channel_id, channel_name, triggers_with_actions, template_id
def create_channel(req_body):
    logger.debug("IN CREATE CHANNEL")

    # validating actor_id
    actor_id = req_body['triggers_with_actions'][0]['action']['actor_id']
    if actor_id == '':
        logger.debug(f'actor_id cannot be blank')
        raise errors.ResourceError(msg=f'actor_id cannot be blank : {body}.')
    try:
        res, debug_msg = t.actors.getActor(actor_id = actor_id,headers={'X-Tapis-Tenant': g.tenant_id},_tapis_debug=True)
    except Exception as e:
        er = e
        msg = er.response.json()
        err_msg = msg['message']
        logger.debug(msg['message'])
        raise errors.ResourceError(msg=f'INVALID actor_id : {err_msg}.')

    logger.debug("actor_id " + actor_id + " is valid. Status is " + res.status)
    channel_id = req_body['channel_id']
    template_id = req_body['template_id']
    if template_id == '': 
        logger.debug(f'template_id cannot be blank')
        raise errors.ResourceError(msg=f'template_id cannot be blank - you can use the public "default_threshold" for and id as an option. : {body}.')
    elif template_id == 'default_threshold':
        template_result={}
        template_result["script"] = f'''from(bucket:"{{bucket_name}}") 
                                        |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
                                        |> filter(fn: (r) => r["_measurement"] == "tsdata")
                                        |> filter(fn: (r) => r["_field"] == "value")
                                        |> filter(fn: (r) => r["inst"] == "{{inst_id}}")
                                        |> filter(fn: (r) => r["site"] == "{{site_id}}")
                                        |> filter(fn: (r) => r["var"] == "{{var_id}}")
                                        |> aggregateWindow(every: 5s, fn: mean, createEmpty: false)
                                    '''
    else:
        try:    
            template_result, template_debug  = get_template(template_id)
        except Exception as e:
            er = e
            msg = er.response.json()
            err_msg = msg['message']
            logger.debug(msg['message'])
            raise errors.ResourceError(msg=f'INVALID template_id : {err_msg}.')
    logger.debug(template_result)
    # create a check task
    # channel_id is same as task_id
    # if task_id already exists in kapacitor, task creation will fail. This will in turn lead to channel creation failure
    
    # task_id = channel_id
    # task_body = {'id': task_id,
    #              'dbrps': [{"db": "chords_ts_production", "rp": "autogen"}], 'status': 'enabled'}

    # task_body['template-id'] = template_id

    # parse condition and convert it to vars for kapacitor template used in task creation
    # vars is of the form :
    vars = {}
    if(isinstance(req_body['triggers_with_actions'][0]['condition'],dict)):
        vars = convert_conditions_to_vars(req_body)
    else:
        logger.debug('No Condition Provided')
        # condn_list = json.loads(json.dumps(req_body['triggers_with_actions'][0]['condition']))
        # lambda_expr, lambda_expr_list, count, expr_list_keys = parse_condition_expr.parse_expr_list(condn_list,'',1,[], [])
        # logger.debug(lambda_expr_list)
        # logger.debug(lambda_expr)
        # vars = parse_condition_expr.convert_condition_list_to_vars( lambda_expr, lambda_expr_list, channel_id)
    #task_body['vars'] = vars
    logger.debug("In Alert - before create Check")
    check_result = checks.create_check(template_result,
                                        site_id=vars['site_id'], 
                                        inst_id=vars['inst_id'],
                                        var_id=vars['var_id'],
                                        check_name=channel_id,
                                        threshold_type=vars['threshold_type'], 
                                        threshold_value=vars['threshold_value'])
    logger.debug(check_result)
    logger.debug("Before create_notification")
    #maybe don't need to create this each time - just fetch one maybe
    notification_endpoint = checks.create_notification_endpoint_actor(endpoint_name=channel_id+'_endpoint', notification_url=conf.tenant[g.tenant_id]['tapis_base_url'] +'/v3/streams/alerts?tenant='+g.tenant_id,actor_id=actor_id)

    notification_rule = checks.create_http_notification_rule(rule_name=channel_id+'_rule', notification_endpoint=notification_endpoint, check_id=check_result.id)
    # create task call to Kapacitor
    #ktask_result, ktask_status = create_task(task_body)
    #logger.debug('Kapacitor task status: ' + str(ktask_status))
    #if ktask_status == 200:
    # if the Kapacitor task is successfully created, sends a request to meta service to store the channel information
    # create request body for meta service
    # it is same as the request received from the user with four added fields: permissions, status, create_time, last_updated
    req_body['permissions'] = {'users': [g.username]}
    req_body['status'] = 'ACTIVE'
    req_body['create_time'] = str(datetime.datetime.utcnow())
    req_body['last_updated'] = str(datetime.datetime.utcnow())
    req_body['check_id'] = check_result.id
    req_body['endpoint_id'] = notification_endpoint.id
    req_body['notifiction_rule_id'] =notification_rule[0].id
    try:
        #create a metadata record with kapacitor task id to the channel metadata collection
        mchannel_result, mchannel_bug = t.meta.createDocument(db=conf.tenant[g.tenant_id]['stream_db'], collection='streams_channel_metadata', request_body=req_body, _tapis_debug=True)
        logger.debug("Status_Code: " + str(mchannel_bug.response.status_code))
        logger.debug(mchannel_result)
        if (str(mchannel_bug.response.status_code) == '201' or str(mchannel_bug.response.status_code) == '200'):
            message = "Channel Created"
            # get the newly created channel object to return
            result, bug = get_channel(req_body['channel_id'])
            logger.debug('Channel Returned From Meta: ' + str(result))
    except:
        raise errors.ResourceError(msg=f'Meta Channel Creation Failed')

    # else:
    #     msg = str(ktask_result) + 'Channel Creation Failed'
    #     raise errors.ResourceError(msg=msg)

    return result, message

# Converts a condition provided by the user to vars for Kapacitor tasks creation API request
# multiple conditions
def convert_conditions_to_vars(req_body):
    logger.debug("CONVERTING condition to vars ...")
    triggers_with_actions = {}
    triggers_with_actions = req_body['triggers_with_actions'][0]

    inst_chords_id ={}
    inst_var_chords_ids = {}

    # inst_id.var_id
    cond_key = []
    cond_key = triggers_with_actions['condition']['key'].split(".")
    # fetch chords id for the instrument
    result = meta.fetch_instrument_index(cond_key[0])
    logger.debug(result)
    vars = {}
    if len(result) > 0:
        logger.debug("inside if")
        logger.debug( str(result['chords_inst_id']))
        inst_chords_id[cond_key[0]] = result['chords_inst_id']

        # fetch chords id for the variable
        result_var, message = meta.get_variable(result['project_id'], result['site_id'], result['instrument_id'], cond_key[1])
        logger.debug("variable chords id : " + str(result_var['chords_id']))
        vars['var_id'] = result_var['chords_id']
        #inst_var_chords_ids[triggers_with_actions['condition']['key']] = result_var['chords_id']
    # create vars dictionary
    result_site, message = meta.get_site(result['project_id'], result['site_id'])
    logger.debug(result_site)
    vars['project_id'] = result['project_id']
    vars['site_id'] = result_site['chords_id']
    vars['inst_id'] = result['chords_inst_id']
    vars['threshold_type'] = triggers_with_actions['condition']['operator'] 
    vars['threshold_value'] = triggers_with_actions['condition']['val']
    
    #vars['crit'] = {}
    #vars['crit']['type'] = "lambda"
    #  value is of the form : "value":"(\"var\" == '1') AND (\"value\" > 91.0)"
    # vars['crit']['value'] = "(\"var\" == '" + str(
    #     inst_var_chords_ids[triggers_with_actions['condition']['key']]) + "') AND (\"value\"" + \
    #                         triggers_with_actions['condition']['operator'] + str(
    #     triggers_with_actions['condition']['val']) + ")"
    # channel id information is added for later processing of the alerts
    #vars["channel_id"] = {"type": "string", "value": req_body['channel_id']}
    logger.debug(vars)
    return vars

def list_channels():
    logger.debug('in Channel list ')
    result= t.meta.listDocuments(db=conf.tenant[g.tenant_id]['stream_db'],collection='streams_channel_metadata',filter='{"permissions.users":"'+g.username+'"}')
    logger.debug(result)
    if len(result.decode('utf-8')) > 0:
        message = "Channels found"
    else:
        raise errors.ResourceError(msg=f'No Channels found')
    logger.debug(result)
    return json.loads(result.decode('utf-8')), message

def get_channel(channel_id):
    logger.debug('In GET Channel' + channel_id)
    logger.debug(g.tenant_id)
    logger.debug(conf.tenant[g.tenant_id]['stream_db'])

    result = t.meta.listDocuments(db=conf.tenant[g.tenant_id]['stream_db'],collection='streams_channel_metadata',filter='{"channel_id":"'+channel_id+'"}')

    if len(result.decode('utf-8')) > 0:
        message = "Channel found."
        channel_result = json.loads(result.decode('utf-8'))[0]
        result = channel_result
        logger.debug("CHANNEL FOUND")
    else:
        logger.debug("NO CHANNEL FOUND")
        raise errors.ResourceError(msg=f'No Channel found')
    return result, message

def update_channel(channel_id, req_body):
    logger.debug('Top of update_channel')
    req_body['channel_id'] = channel_id

    # Get channel information from Meta
    try:
        channel_result, msg = get_channel(channel_id)
    except Exception as e:
        msg = f" Channel {channel_id} NOT Found; exception: {e}"
        raise errors.ResourceError(msg=msg)

    # TODO check if Kapacitor Task exist
    logger.debug('UPDATING ... Kapacitor Task')
    task_id = channel_id
    task_body = {'id': task_id,
                 'dbrps': [{"db": "chords_ts_production", "rp": "autogen"}]}

    task_body['template-id'] = req_body['template_id']
    vars = {}
    vars = convert_conditions_to_vars(req_body)
    task_body['vars'] = vars
    logger.debug('update_task request body: ' + str(task_body))

    try:
        kapacitor_result, kapacitor_status_code = update_kapacitor_task(channel_id, task_body)
    except Exception as e:
        msg = f" Not able to connect to Kapacitor for the task {channel_id} update; exception: {e}"
        raise errors.ResourceError(msg=msg)

    if kapacitor_status_code == 200:
        logger.debug("UPDATED ... Kapacitor task  ")
        logger.debug("UPDATING ... channel object in meta")

        if kapacitor_result['status'] == 'enabled':
            channel_result['status'] = 'ACTIVE'
        elif kapacitor_result['status'] == 'disabled':
            channel_result['status'] = 'INACTIVE'
        else:
            channel_result['status'] = 'ERROR'
        channel_result['last_updated'] = str(datetime.datetime.utcnow())
        channel_result['template_id'] = kapacitor_result['template-id']
        channel_result['channel_name'] = req_body['channel_name']
        channel_result['triggers_with_actions'] = req_body['triggers_with_actions']
        meta_result = {}
        meta_result, meta_message = meta.update_channel(channel_result)
    else:
        str_response = kapacitor_result['error']
        msg = f" Could Not Find Channel {channel_id} with Task ID {channel_result['channel_id']}: {str_response} "
        logger.debug(msg)
        raise errors.ResourceError(msg=msg)
    return meta_result, meta_message

def update_channel_status(channel_id, body):
    logger.debug('In update_channel_status')
    try:
        channel_result, msg = get_channel(channel_id)
    except Exception as e:
        msg = f" Channel {channel_id} NOT Found; exception: {e}"
        raise errors.ResourceError(msg=msg)

    logger.debug('UPDATING ... Kapacitor task status')
    result = {}
    meta_result = {}
    try:
        result,status_code = change_task_status(channel_result['channel_id'],body)
    except Exception as e:
        msg = f" Not able to connect to Kapacitor for the task {channel_result['channel_id']} status update; exception: {e}"
        raise errors.ResourceError(msg=msg)

    if status_code == 200:
        logger.debug("UPDATED ... Kapacitor task status ")
        logger.debug("UPDATING ... channel object in meta")
        logger.debug('status: ' + body['status'])

        # TODO Convert to Status Enum
        if result['status']=='enabled':
            channel_result['status'] = 'ACTIVE'
        elif result['status']=='disabled':
            channel_result['status'] = 'INACTIVE'
        else:
            channel_result['status'] = 'ERROR'
        channel_result['last_updated'] = str(datetime.datetime.utcnow())
        meta_result, message = meta.update_channel(channel_result)
    else:
        str_result = result['error']
        msg = f" Could Not Find Channel {channel_id} with Task {channel_result['channel_id']} kapacitor's response:{str_result} "
        logger.debug(msg)
        raise errors.ResourceError(msg=msg)
    return meta_result,message

def remove_channel():
    return True

################### ALERT ############################################
def create_alert():
    return True

def get_alert():
    return True

def list_alerts():
    return True

################### TEMPLATE ##########################################

# create templates
def create_template(body):
    logger.debug("IN CREATE TEMPLATE")
    body['create_time'] = str(datetime.datetime.utcnow())
    body['last_updated'] = str(datetime.datetime.utcnow())
    body['permissions'] = {'users': [g.username]}

    try:
        mtemplate_result, mtemplate_bug =t.meta.createDocument(db=conf.tenant[g.tenant_id]['stream_db'], collection='streams_templates_metadata', request_body=body, _tapis_debug=True)
        logger.debug("Status_Code: " + str(mtemplate_bug.response.status_code))
        logger.debug(mtemplate_result)
        if str(mtemplate_bug.response.status_code) == '201' :
            message = "Template Created in Meta"
            #get the newly created template object to return
            result, bug = get_template(body['template_id'])
            logger.debug(result)
    except:
        message = f'Template Creation in Meta Failed'
        if (res_delete_template.status_code == 204):
            logger.debug(f'Kapacitor template deleted')
        else:
            logger.debug(f'kapacitoe template not deleted')
        raise errors.ResourceError(msg=message)


    return result, message

# get template
def get_template(template_id):
    logger.debug('In get_template')
    result = {}
    #Insure user permissions in the Meta records
    result = t.meta.listDocuments(db=conf.tenant[g.tenant_id]['stream_db'], collection='streams_templates_metadata',filter='{"template_id":"' + template_id + '", "permissions.users":"'+ g.username+'"}')
    logger.debug(len(result.decode('utf-8')))
    if len(result.decode('utf-8')) > 2:
        message = "Template found."
        template_result = json.loads(result.decode('utf-8'))[0]
        result = template_result
        logger.debug("TEMPLATE FOUND")
    else:
        logger.debug("NO TEMPLATE FOUND")
        raise errors.ResourceError(msg=f'No TEMPLATE found matching id: '+template_id)
    return result, message

def update_template(template_id, body):
    logger.debug('In update_template')
    try:
        meta_template, msg = get_template(template_id)
    except Exception as e:
       msg = f" Template {template_id} NOT Found; exception: {e}"
       raise errors.ResourceError(msg=msg)

    logger.debug('UPDATING ... Kapacitor Template')

    template_body = {}
    template_body['id'] = template_id
    template_body['type'] = body['type']
    template_body['script'] = body['script']

    try:
        logger.debug('Try to update k-template')
        result,status_code = update_kapacitor_template(template_id,template_body)
    except Exception as e:
        logger.debug('Updating k-template failed: {e}')
        msg = f" Not able to connect to Kapacitor for the template {body['template_id']} update; exception: {e}"
        raise errors.ResourceError(msg=msg)

    if status_code == 200:
        logger.debug("UPDATED ... Kapacitor template ")
        logger.debug("UPDATING ... template object in meta")
        meta_template['type'] = body['type']
        meta_template['script'] = body['script']
        meta_template['last_updated'] = str(datetime.datetime.utcnow())
        result = {}
        result, message = meta.update_template(meta_template)
    else:
        msg = f" Could Not Find Template {template_id} with Template {body} "
        raise errors.ResourceError(msg=msg)
    return result,message


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
def list_kapacitor_templates():
    logger.debug("IN LIST TEMPLATES")
    headers={'content_type': 'application/json'}
    res = requests.get(conf.kapacitor_url + '/kapacitor/v1/templates', auth=HTTPBasicAuth(conf.kapacitor_username, conf.kapacitor_password), verify=False )
    return json.loads(res.content),res.status_code

#get a template
def get_template_kapacitor(template_id):
    logger.debug("IN GET TEMPLATE")
    headers={'content_type': 'application/json'}
    res = requests.get(conf.kapacitor_url + '/kapacitor/v1/templates/' + template_id, auth=HTTPBasicAuth(conf.kapacitor_username, conf.kapacitor_password), verify=False)
    return json.loads(res.content),res.status_code

def update_kapacitor_template(template_id,body):
    logger.debug("UPDATING Template")
    logger.debug(conf.kapacitor_url + '/kapacitor/v1/templates/' + template_id)


    logger.debug(body)
    headers = {
        'content-type': "application/json"
    }
    logger.debug(headers)
    try:
        res = requests.patch(conf.kapacitor_url + '/kapacitor/v1/templates/' + template_id, headers=headers, json=body,
                       auth=HTTPBasicAuth(conf.kapacitor_username, conf.kapacitor_password), verify=False)
    except Exception as e:
        msg = f" Kapacitor bad request ; exception: {e}"
        raise errors.ResourceError(msg=msg)
    logger.debug('Kapacitor Response' + str(res.content))
    logger.debug('status_code' + str(res.status_code))
    return json.loads(res.content), res.status_code

def remove_template():
    return True

############################ CHANNEL INDEX #############################
def create_channel_index(project_id, channel_id):
    req_body = {'project_id':project_id, 'channel_id': channel_id}
    result, bug =t.meta.createDocument(db=conf.tenant[g.tenant_id]['stream_db'], collection='streams_channel_index', request_body=req_body, _tapis_debug=True)
    return result, str(bug.response.status_code)

def fetch_channel_index(channel_id):
    result= t.meta.listDocuments(db=conf.tenant[g.tenant_id]['stream_db'],collection='streams_channel_index',filter='{"channel_id":"'+channel_id+'"}')
    return json.loads(result.decode('utf-8'))
