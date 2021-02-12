import datetime
import requests
import json
from service import auth
from service import meta
import uuid

from flask import g, Flask
app = Flask(__name__)

from common import utils, errors

# get the logger instance -
from common.logs import get_logger
logger = get_logger(__name__)
from service import parse_condition_expr


# access the tapipy instance
t = auth.t


'''
Integration with Abaco
When a measurement is written to influxDB, it copied to Kapacitor through subscription. If the boolean conditional expression defined
in the Channel definition is evaluated to be true, an alert is raised and the data generating the alert is send to the Stream API. 
Streams Service sends these alerts/critical data in a request for execution of the pre-registered Abaco actor specified in the Channel definition.
Abaco receives the request and sends back response with an executionId
Streams service uses it to create an alert for the user to check.
This method creates an alert with the information received from Kapacitor alert data and from Abacos's response.
'''
def create_alert(channel, req_data):
    actor_id = channel['triggers_with_actions'][0]['action']['actor_id']
    logger.debug('actor_id:' + actor_id)

     # prepare request for abaco
    message_data = {}
    message_data['message'] = req_data
    message_data['message']['channel_id'] = channel['channel_id']
    logger.debug('message_data so far ~~~: '+ str(message_data))
    logger.debug('Fetching from Meta')
    result = meta.fetch_instrument_index(channel["triggers_with_actions"][0]['inst_ids'][0])
    logger.debug(str(result))
    message_data['message']['project_id'] = result['project_id']
    message_data['message']['site_id'] = result['site_id']
    message_data['message']['inst_id'] = result['instrument_id']

    # single condition
    if (isinstance(channel['triggers_with_actions'][0]['condition'], dict)):
        cond_key = channel['triggers_with_actions'][0]['condition']['key'].split(".")
        message_data['message']['var_id'] = cond_key[1]
    # multiple conditions
    else:
        condn_list = json.loads(json.dumps(channel['triggers_with_actions'][0]['condition']))
        logger.debug( condn_list)
        lambda_expr, lambda_expr_list, count, expr_list_keys = parse_condition_expr.parse_expr_list(condn_list, '', 1,[],[])
        logger.debug(expr_list_keys)
        message_data['message']['var_ids']=[]
        for i in range(len(expr_list_keys)):
            expr = {}
            cond_expr_key = expr_list_keys[i][1].split(".")
            expr['inst_id'] = cond_expr_key[0]
            expr['var_id'] = cond_expr_key[1]
            message_data['message']['var_ids'].append(expr)
        cond_expr_key = expr_list_keys[0][1].split(".")

        message_data['message']['var_id'] = cond_expr_key[1]

    logger.debug('message_data: '+ str(message_data))

    # send request to Abaco with the nonce
    try:
        res, debug_msg = t.actors.sendMessage(actor_id=actor_id, request_body= json.dumps(message_data), headers={'X-Tapis-Tenant': g.tenant_id, "Content-Type":"application/json"},_tapis_debug=True)
    except Exception as e:
        er = e
        logger.debug(er.request.url)
        logger.debug(er.request.headers)
        logger.debug(er.response.json())
        msg = f"Got exception trying to post message to Abaco actor: {actor_id}; exception: {e}"
        raise errors.BaseTapyException(msg=msg, request=res.request)
    logger.debug('abaco response status code:' + str(debug_msg.response.status_code))
    logger.debug(debug_msg.request.body)
    logger.debug(debug_msg.request.headers)
    if str(debug_msg.response.status_code) == '200':
        # create alert response data
        logger.debug("saving executionId from Abaco and generating alert...")
        execution_id =  res.executionId
        alert = {}
        alert['alert_id'] = str(uuid.uuid4())
        alert['channel_name'] = channel['channel_name']
        alert['channel_id'] = channel['channel_id']
        alert['actor_id'] = actor_id
        alert['execution_id'] = execution_id
        alert['message'] = req_data['message']
        alert['create_time'] = str(datetime.datetime.utcnow())
        logger.debug(alert)
        # send alert response data to Meta V3
        alert_result, msg = meta.create_alert(alert)
        if msg == "Alert Added":
            logger.debug(alert_result)
            result = meta.strip_meta(alert_result)
            logger.debug(result)
            return result, msg
        else:
            err_msg = f" Failed to add Alert for{channel['channel_id']} in Meta"
            raise errors.ResourceError(msg=err_msg)
    else:
        msg = f"Abaco Actor: {actor_id} unable to perform the execution on the message: {message_data}. Check the Actor Status and the message"
        raise errors.ResourceError(msg=msg)
