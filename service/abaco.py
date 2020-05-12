import requests
from flask import g, Flask
from common.config import conf
app = Flask(__name__)

from common import utils, errors
# get the logger instance -
from common.logs import get_logger
logger = get_logger(__name__)

import auth
import meta
import json
#access the dynatpy instance
t = auth.t
# "message=var1 exceeded"
# https: // api.tacc.utexas.edu / actors / v2 /$ACTOR_ID / messages?x - nonce = TACC - PROD_XV4XQDyp6jRLj
def create_alert(channel,req_data):
    actor_id = channel['triggers_with_actions'][0]['action']['actor_id']
    abaco_base_url = channel['triggers_with_actions'][0]['action']['abaco_base_url']
    abaco_nonce = channel['triggers_with_actions'][0]['action']['nonces']
    abaco_url = abaco_base_url + '/actors/v2' + actor_id + '/messages?x-nonce=' + abaco_nonce
    headers = {'accept': 'application/json'}
    res = requests.post(abaco_url, data=req_data, headers=headers, verify=False)
    logger.debug(res.content)
    logger.debug(res.status_code)
    if res.status_code == 200:
        abaco_res = json.loads(res.content.decode('utf-8'))
        execution_id = abaco_res['result']['executionId']
        alert = {}
        alert['channel_name'] = channel['channel_name']
        alert['channel_id'] = channel['channel_id']
        alert['actor_id'] = channel['triggers_with_actions'][0]['action']['actor_id']
        alert['execution_id'] = execution_id
        alert_result, msg = meta.create_alert(alert)
        result = meta.strip_meta(alert_result)
        return result, msg
    else:
        raise errors.ResourceError(msg=f'No Abaco Actor found')
