

import json

global logical_op
logical_op = [] # a stack of operators
global state
state = ''

#----------- Example of condn expression ----------------------------------------------
cond_expr = ["AND",{"key":"1bclocal.templocal1", "op":">", "val":91.0},
                       ["OR",{"key":"1bclocal.templocal2", "op":">", "val":200.0},
                        {"key":"1bclocal.templocal3", "op":"<", "val":100.0}
                        ]
             ]
#---------------------------------------------------------------------------------------

c=json.loads(json.dumps(cond_expr))

exp_list = c

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


expr_to_lambda(exp_list)
print('\n')
print(lambda_expr)

#lambda_expr=''


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
            lambda_expr = lambda_expr + 'var'+str(count)+'.value' + ' ' + exp_list[i]['op'] + ' ' + 'th'+str(count) + ' '
            chords_id = get_chords_id(exp_list[i]['key'])
            inter =  "(\"var\" == '"+ str(chords_id)+"') AND (\"value\""+ exp_list[i]['op'] +str(exp_list[i]['val'])+")"
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


lambda_expr,lambda_expr_list=get_all_crit_vars(exp_list,'',[],'',1,[])
print('\n')
print(lambda_expr)
print(lambda_expr_list)

##### -------

def convert_condition_list_to_vars( lambda_expr, lambda_expr_list, channel_id):
    #logger.debug("CONVERTING condition lisr to vars ...")
    vars = {}
    vars["channel_id"] = {"type": "string", "value": channel_id}
    for i in range(len(lambda_expr_list)):
        vars['crit'+str(lambda_expr_list[i][0])] = {}
        vars['crit'+str(lambda_expr_list[i][0])]['type'] = "lambda"
        #  value is of the form : "value":"(\"var\" == '1') AND (\"value\" > 91.0)"
        vars['crit'+str(lambda_expr_list[i][0])]['value'] = lambda_expr_list[i][2]
        # channel id information is added for later processing of the alerts

        vars['th'+ str(lambda_expr_list[i][0])] = {}
        vars['th' + str(lambda_expr_list[i][0])]['type'] = "float"
        vars['th' + str(lambda_expr_list[i][0])]['value'] = lambda_expr_list[i][3]
    vars['crit'] = {}
    vars['crit']['type'] = "lambda"
    vars['crit']['value'] = lambda_expr
    return vars

vars= {}
vars = convert_condition_list_to_vars( lambda_expr, lambda_expr_list, "test_channel")
print(vars)
###---------------------
def get_all_crit_vars(exp_list,state,logical_op, lambda_expr,count):

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
            lambda_expr = lambda_expr + 'var'+str(count)+'.value' + ' ' + exp_list[i]['op'] + ' ' + 'th'+str(count) + ' '
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
            lambda_expr = get_all_crit_vars(exp_list[i],state,logical_op,lambda_expr,count)
    return lambda_expr


lambda_expr=get_all_crit_vars(exp_list,'',[],'',1)
print('\n')
print(lambda_expr)