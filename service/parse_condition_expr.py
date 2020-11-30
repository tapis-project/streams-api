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

t = auth.t


global logical_op
logical_op = [] # a stack of operators
global state
state = ''

#----------- Example of condn expression ----------------------------------------------
#cond_expr = ["AND",{"key":"1bclocal.templocal1", "op":">", "val":91.0},
#                       ["OR",{"key":"1bclocal.templocal2", "op":">", "val":200.0},
#                        {"key":"1bclocal.templocal3", "op":"<", "val":100.0}
#                        ]
#             ]
#---------------------------------------------------------------------------------------

#c=json.loads(json.dumps(cond_expr))

#exp_list = c

global lambda_expr

lambda_expr=''

def expr_to_lambda(exp_list):
    global state

    global lambda_expr
    for i in range(len(exp_list)):
        #print("i = " + str(i))
        logical_op_in_exp_list0 = exp_list[0]
        if i==0: # --When i is 0, look into the state variable to decide if you would want to append the logical operator
                  # --( print
            if logical_op_in_exp_list0 == "NOT":
                #print("NOT", end=' ')
                #print('(', end=' ')
                lambda_expr = lambda_expr + 'NOT' + '('
                state = "NOT"
            else:
                logical_op.append((logical_op_in_exp_list0,len(exp_list)-2))
                if state != logical_op_in_exp_list0 and state !='' and state !='NOT':
                    #print('(', end=' ')
                    lambda_expr = lambda_expr + '('
                state = logical_op_in_exp_list0
            continue
        elif isinstance(exp_list[i], dict):
            #---print('trying to parse' + str(exp_list[i]))
            #print(exp_list[i]['key'],end = ' ')
            #print(exp_list[i]['op'],end = ' ')
            #print(exp_list[i]['val'],end = ' ')

            lambda_expr = lambda_expr + exp_list[i]['key'] + ' ' + exp_list[i]['op']+' ' + str(exp_list[i]['val']) + ' '
            if i == (len(exp_list) - 1):
                #print(')', end=' ')
                lambda_expr = lambda_expr + ')'

            if len(logical_op) != 0 and state != 'NOT':
                op,opn = logical_op.pop()
                if op!='NOT':
                    #print(op,end = ' ')
                    lambda_expr = lambda_expr + op + ' '
                opn = opn - 1
                state = op
                if opn > 0:
                    logical_op.append((op,opn))


        else:
            #print('trying to parse' + str(exp_list[i]))
            expr_to_lambda(exp_list[i])


#expr_to_lambda(exp_list)
#print('\n')
#print(lambda_expr)

#lambda_expr=''

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
        logger.debug(" chords instrument_ id: " + str(result[0]['chords_inst_id']))
        #inst_chords_id[cond_key[0]] = result[0]['chords_inst_id']
        #inst_chords_id[cond_key[0]] = result[0]['instrument_id']

        # fetch chords id for the variable
        result_var, message = meta.get_variable(result[0]['project_id'], result[0]['site_id'],
                                                result[0]['instrument_id'], cond_key[1])
        logger.debug("variable chords id : " + str(result_var['chords_id']))
        inst_var_chords_ids[key] = result_var['chords_id']
        return result[0]['chords_inst_id'],result_var['chords_id']

def get_chords_id(key):
    keys_value={"1bclocal.templocal1": 1,
                "1bclocal.templocal2": 2,
                "1bclocal.templocal3": 3
                }
    return keys_value[key]

def get_all_crit_vars(exp_list,state,logical_op, lambda_expr,count,lambda_expr_list):

    for i in range(len(exp_list)):
        logical_op_in_exp_list0 = exp_list[0]
        if i==0: # --When i is 0, look into the state variable to decide if you would want to append the logical operator
            if logical_op_in_exp_list0 == "NOT":
                lambda_expr = lambda_expr + 'NOT' + '('
                state = "NOT"
            else:
                logical_op.append((logical_op_in_exp_list0,len(exp_list)-2))
                if state != logical_op_in_exp_list0 and state !='' and state !='NOT':
                    lambda_expr = lambda_expr + '('
                state = logical_op_in_exp_list0
            continue
        elif isinstance(exp_list[i], dict):
            #lambda_expr = lambda_expr + 'var'+str(count)+'.value' + ' ' + exp_list[i]['op'] + ' ' + 'th'+str(count) + ' '
            #lambda_expr = lambda_expr + 'var' + str(count) + '.value' + ' ' + exp_list[i]['operator'] + ' ' + str(exp_list[i]['val']) + ' '
            #lambda_expr = lambda_expr + "(\""+'var' + str(count) + '.value' + "\")"+ ' ' + exp_list[i]['operator'] + ' ' + str(
             #   exp_list[i]['val']) + ' '
            lambda_expr = lambda_expr + "\"" + 'var' + str(count) + '.value' + "\"" + ' ' + exp_list[i][
                'operator'] + ' ' + str(
                exp_list[i]['val']) + ' '
            #chords_id = get_chords_id(exp_list[i]['key'])
            logger.debug("key: " + exp_list[i]['key'])
            chords_id = get_chords_id_for_variable(exp_list[i]['key'])
            #inter =  "(\"var\" == '"+ str(chords_id)+"') AND (\"value\""+ exp_list[i]['operator'] +str(exp_list[i]['val'])+")"
            inter = "(\"var\" == '" + str(
        chords_id) + "') AND (\"value\"" + \
                            exp_list[i]['operator'] + str(exp_list[i]['val']) + ")"
            lambda_expr_list.append((count,chords_id,inter,exp_list[i]['val']))
            #lambda_expr = lambda_expr + exp_list[i]['key'] + ' ' + exp_list[i]['op']+' ' + str(exp_list[i]['val']) + ' '

            count = count + 1
            if i == (len(exp_list) - 1):
                lambda_expr = lambda_expr + ')'

            if len(logical_op) != 0 and state != 'NOT':
                op,opn = logical_op.pop()
                if op!='NOT':
                   lambda_expr = lambda_expr + op + ' '
                opn = opn - 1
                state = op
                if opn > 0:
                    logical_op.append((op,opn))
        else:
            lambda_expr, lambda_expr_list = get_all_crit_vars(exp_list[i],state,logical_op,lambda_expr,count,lambda_expr_list)
    return lambda_expr,lambda_expr_list


#lambda_expr,lambda_expr_list=get_all_crit_vars(exp_list,'',[],'',1,[])
#print('\n')
#print(lambda_expr)
#print(lambda_expr_list)

##### -------

def convert_condition_list_to_vars( lambda_expr, lambda_expr_list, channel_id):
    #logger.debug("CONVERTING condition lisr to vars ...")
    vars = {}
    vars["channel_id"] = {"type": "string", "value": channel_id}
    vars["measurement"] = {"type":"string","value":"tsdata"}

    for i in range(len(lambda_expr_list)):
        logger.debug("i: "+ str(i)+ ",  cond1: "+ str(lambda_expr_list[i][0])+ ",  expr: "+lambda_expr_list[i][2])
        vars['crit'+str(lambda_expr_list[i][0])] = {}
        vars['crit'+str(lambda_expr_list[i][0])]['type'] = "lambda"
        #  value is of the form : "value":"(\"var\" == '1') AND (\"value\" > 91.0)"
        vars['crit'+str(lambda_expr_list[i][0])]['value'] = lambda_expr_list[i][2]
        # channel id information is added for later processing of the alerts

        #vars['th'+ str(lambda_expr_list[i][0])] = {}
        #vars['th' + str(lambda_expr_list[i][0])]['type'] = "float"
        #vars['th' + str(lambda_expr_list[i][0])]['value'] = lambda_expr_list[i][3]
    vars['crit'+str(lambda_expr_list[i][0]+1)] = {}
    vars['crit'+str(lambda_expr_list[i][0]+1)]['type'] = "lambda"
    vars['crit'+str(lambda_expr_list[i][0]+1)]['value'] = lambda_expr
    return vars

#vars= {}
#vars = convert_condition_list_to_vars( lambda_expr, lambda_expr_list, "test_channel")
#print(vars)

def parse_expr_list(exp_list, lambda_expr, count, lambda_expr_list, expr_list_keys):
    if isinstance(exp_list, dict):
        lambda_expr = lambda_expr + "\"" + 'var' + str(count) + '.value' + "\"" + ' ' + exp_list[
            'operator'] + ' ' + str(exp_list['val']) + ' '
        #lambda_expr = lambda_expr + ' '+ exp_list['key'] + ' ' + exp_list['operator'] + ' ' + str(exp_list['val'])
        #print(exp_list['key'], end=' ')
        #print(exp_list['op'], end=' ')
        #print(exp_list['val'], end=' ')
        #chords_id = get_chords_id(exp_list['key'])
        chords_inst_id,chords_var_id = get_chords_id_for_variable(exp_list['key'])
        inter = "(\"var\" == '" + str(chords_var_id) + "') AND (\"inst\" == '" + str(chords_inst_id) + "')"
        lambda_expr_list.append((count, chords_var_id, inter, exp_list['val']))
        # with key
        expr_list_keys.append((count,exp_list['key']))
        count = count + 1
    else:
        len_exp_list = len(exp_list)
        if len_exp_list == 3:
            #print('(', end=' ')
            lambda_expr = lambda_expr + ' ('
            lambda_expr, lambda_expr_list, count, expr_list_keys = parse_expr_list(exp_list[1],lambda_expr,count,lambda_expr_list, expr_list_keys)
            #print(')', end=' ')
            lambda_expr = lambda_expr + ')'
            print(exp_list[0], end=' ')
            lambda_expr = lambda_expr + ' ' + exp_list[0]
            lambda_expr = lambda_expr + ' ('
            #print('(', end=' ')
            lambda_expr, lambda_expr_list, count, expr_list_keys = parse_expr_list(exp_list[2],lambda_expr,count,lambda_expr_list, expr_list_keys)
            #print(')', end=' ')
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