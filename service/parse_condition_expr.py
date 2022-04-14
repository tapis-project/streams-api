import requests
import json
import datetime
from flask import g, Flask
from tapisservice.tapisflask.utils import conf
app = Flask(__name__)
from tapisservice.tapisflask import utils
from tapisservice import errors
# get the logger instance -
from tapisservice.logs import get_logger
logger = get_logger(__name__)
from service import auth
from requests.auth import HTTPBasicAuth
import subprocess
from service import meta

t = auth.t

#----------- Example of condn_list expression ----------------------------------------------
#  cond_expr = ["AND",{"key":"1bclocal.templocal1", "op":">", "val":91.0},
#                       ["OR",{"key":"1bclocal.templocal2", "op":">", "val":200.0},
#                        {"key":"1bclocal.templocal3", "op":"<", "val":100.0}
#                        ]
#             ]
#---------------------------------------------------------------------------------------

# Get CHORDS ID for instrument and variable
def get_chords_id_for_variable(key):
    inst_chords_id = {}
    inst_var_chords_ids = {}

    # inst_id.var_id
    cond_key = []
    cond_key = key.split(".")
    #cond_key = triggers_with_actions['condition']['key'].split(".")
    # fetch chords id for the instrument
    result = meta.fetch_instrument_index(cond_key[0])
    logger.debug(result)
    if len(result) > 0:
        logger.debug(" chords instrument_ id: " + str(result['chords_inst_id']))
        # fetch chords id for the variable
        result_var, message = meta.get_variable(result['project_id'], result['site_id'],
                                                result['instrument_id'], cond_key[1])
        logger.debug("variable chords id : " + str(result_var['chords_id']))
        inst_var_chords_ids[key] = result_var['chords_id']
        return result['chords_inst_id'], result_var['chords_id']

#Convert condition list template variable list
def convert_condition_list_to_vars( lambda_expr, lambda_expr_list, channel_id):
    #logger.debug("CONVERTING condition lisr to vars ...")
    vars = {}
    vars["channel_id"] = {"type": "string", "value": channel_id}
    vars["measurement"] = {"type":"string","value":"tsdata"}

    for i in range(len(lambda_expr_list)):
        logger.debug("i: "+ str(i)+ ",  cond1: "+ str(lambda_expr_list[i][0])+ ",  expr: "+lambda_expr_list[i][2])
        vars['crit'+str(lambda_expr_list[i][0])] = {}
        vars['crit'+str(lambda_expr_list[i][0])]['type'] = "lambda"
        #  value is of the form : "value":"(\"var\" == '1') AND (\"inst\" == '12')"
        vars['crit'+str(lambda_expr_list[i][0])]['value'] = lambda_expr_list[i][2]
        # channel id information is added for later processing of the alerts

    vars['crit'+str(lambda_expr_list[i][0]+1)] = {}
    vars['crit'+str(lambda_expr_list[i][0]+1)]['type'] = "lambda"
    vars['crit'+str(lambda_expr_list[i][0]+1)]['value'] = lambda_expr
    return vars



def parse_expr_list(exp_list, lambda_expr, count, lambda_expr_list, expr_list_keys):
    if isinstance(exp_list, dict):
        lambda_expr = lambda_expr + "\"" + 'var' + str(count) + '.value' + "\"" + ' ' + exp_list[
            'operator'] + ' ' + str(exp_list['val']) + ' '

        chords_inst_id,chords_var_id = get_chords_id_for_variable(exp_list['key'])
        inter = "(\"var\" == '" + str(chords_var_id) + "') AND (\"inst\" == '" + str(chords_inst_id) + "')"
        lambda_expr_list.append((count, chords_var_id, inter, exp_list['val']))
        # with key
        expr_list_keys.append((count,exp_list['key']))
        count = count + 1
    else:
        len_exp_list = len(exp_list)
        if len_exp_list == 3:
            lambda_expr = lambda_expr + ' ('
            lambda_expr, lambda_expr_list, count, expr_list_keys = parse_expr_list(exp_list[1],lambda_expr,count,lambda_expr_list, expr_list_keys)
            lambda_expr = lambda_expr + ')'
            lambda_expr = lambda_expr + ' ' + exp_list[0]
            lambda_expr = lambda_expr + ' ('
            lambda_expr, lambda_expr_list, count, expr_list_keys = parse_expr_list(exp_list[2],lambda_expr,count,lambda_expr_list, expr_list_keys)
            lambda_expr = lambda_expr + ')'

        elif len_exp_list > 3:
            operator = exp_list[0]
            for i in range(1,(len_exp_list-1)):
                print('(', end=' ')
                lambda_expr = lambda_expr + '('
                lambda_expr, lambda_expr_list, count, expr_list_keys = parse_expr_list(exp_list[i],lambda_expr,count,lambda_expr_list, expr_list_keys)
                lambda_expr = lambda_expr + ')'
                print(')', end=' ')
                print(operator, end=' ')
                lambda_expr = lambda_expr + ' ' + operator
            print('(', end=' ')
            lambda_expr = lambda_expr + '('
            lambda_expr, lambda_expr_list, count, expr_list_keys = parse_expr_list(exp_list[len_exp_list-1],lambda_expr,count,lambda_expr_list, expr_list_keys)
            print(')', end=' ')
            lambda_expr = lambda_expr + ')'
        else:
            print('NOT', end=' ')
            print('(', end=' ')
            lambda_expr = lambda_expr + ' NOT ('
            lambda_expr, lambda_expr_list, count, expr_list_keys  = parse_expr_list(exp_list[1],lambda_expr,count,lambda_expr_list, expr_list_keys)
            print(')', end=' ')
            lambda_expr = lambda_expr + ')'
    return lambda_expr, lambda_expr_list, count, expr_list_keys
