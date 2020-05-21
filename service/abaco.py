import datetime
import requests
import json
import auth
import meta
from flask import g, Flask
app = Flask(__name__)

from common import utils, errors
# get the logger instance -
from common.logs import get_logger
logger = get_logger(__name__)


#access the dynatpy instance
t = auth.t

def create_alert(channel,req_data):
    actor_id = channel['triggers_with_actions'][0]['action']['actor_id']
    logger.debug(actor_id)
    abaco_base_url = channel['triggers_with_actions'][0]['action']['abaco_base_url']
    abaco_nonce = channel['triggers_with_actions'][0]['action']['nonces']
    abaco_url = abaco_base_url + '/actors/v2/' + actor_id + '/messages?x-nonce=' + abaco_nonce
    logger.debug(abaco_url)
    headers = {'accept': 'application/json'}
    message_data = {}
    message_data['message'] = req_data
    try:
        res = requests.post(abaco_url, json=message_data, headers=headers, verify=False)
    except Exception as e:
        msg = f"Got exception trying to post message to Abaco actor: {actor_id}; exception: {e}"
        raise errors.BaseTapyException(msg=msg, request=res.request)

    logger.debug(res.content)
    logger.debug(res.status_code)

    if res.status_code == 200:
        abaco_res = json.loads(res.content.decode('utf-8'))
        execution_id = abaco_res['result']['executionId']
        alert = {}
        alert['alert_id'] = execution_id
        alert['channel_name'] = channel['channel_name']
        alert['channel_id'] = channel['channel_id']
        alert['actor_id'] = actor_id
        alert['execution_id'] = execution_id
        alert['create_time'] = str(datetime.datetime.utcnow())
        logger.debug(alert)
        alert_result, msg = meta.create_alert(alert)
        logger.debug(alert_result)
        result = meta.strip_meta(alert_result)
        logger.debug(result)
        return result, msg
    else:
        msg = f"Abaco Actor: {actor_id} unable to perform the execution on the message: {message_data}. Check the Actor Status and the message"
        raise errors.ResourceError(msg=msg)
