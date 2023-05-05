import requests
import json
import datetime
from flask import g, Flask
from tapisservice.config import conf
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


def args_parse(request):
    logger.info(f'Inside args_parse')
    query = request.args.to_dict(flat=False)
    logger.info(f'Searching for: {query}')
    operators= ['neq', 'eq', 'lte', 'lt','gte','gt', 'nin','in']
    project_params = ['project_name', 'project_id', 'owner', 'pi', 'funding_resource', 'project_url', 'active', 'created_at', 'last_updated']
    # [(['project_id', 'in'], ['test']), (['owner', 'neq'], ['test1'])]
    search_list = [(k.split('.'), v) for k, v in query.items()]
    logger.info(search_list)
    constructed_query = []
    # validation of search parameters
    for i in (0,len(search_list)-1):
        if(search_list[i][0][0] not in project_params):
                raise errors.ResourceError(msg=f'Invalid search parameter: {search_list[i][0][0]}.')
        if(search_list[i][0][1] not in operators):
                raise errors.ResourceError(msg=f'Invalid operator: {search_list[i][0][1]}.')
        constructed_query.append([search_list[i][0][0],search_list[i][0][1],str(search_list[i][1]).strip('[,\',]')])
    #logger.info(f' query constructed ')
    return constructed_query

def build_mongo_search_query(mongo_find, param, operator,search_value):
    if(operator == 'eq'):
        mongo_find = mongo_find+ '"' + param + '":' + '"' + search_value +'"'
    elif(operator == 'neq'):
        mongo_find = mongo_find+ '"' + param + '":' + '{$ne:' + search_value +'}}'
    elif(operator == 'lt'):
        mongo_find = mongo_find+ '"' + param + '":' + '{$lt:' + search_value +'}}'
    elif(operator == 'lte'):
        mongo_find = mongo_find+ '"' + param + '":' + '{$lte:' + search_value +'}}'
    elif(operator == 'gt'):
        mongo_find = mongo_find+ '"' + param + '":' + '{$gt:' + search_value +'}}'
    elif(operator == 'gte'):
        mongo_find = mongo_find+ '"' + param + '":' + '{$gte:' + search_value +'}}'
    elif(operator == 'in'):
        mongo_find = mongo_find+ '"' + param + '":' + '{$lt:' + search_value +'}}'
    logger.info(mongo_find) 
    return mongo_find


#Example: curl -H "X-Tapis-Token:$jwt" http://localhost:5000/v3/streams/project?'project_id.eq=test_project2023-03-06T11:33:52.178730&owner=testuser2'
'''
 Possible search parameters are: project_name, project_id, owner, 
 pi, funding_resource, project_url, active, created_at, last_updated

'''
def project_search(request):
    logger.info(f'Inside project_search')
    args_list = args_parse(request)
    logger.info(args_list)
    #all_projects= meta.list_projects(100,0)
    #logger.info(all_projects)
   # project_data=json.dumps(all_projects[0])
    if (len(args_list) > 0):
        try:
            mongo_find = '{'
            for i in range (0,len(args_list)):
                param=args_list[i][0]
                operator=args_list[i][1]
                search_value=args_list[i][2]
                logger.info(f'param: {param} operator: {operator} search_value: {search_value}')
                mongo_find = build_mongo_search_query(mongo_find, param,operator,search_value )
                #mongo_find = mongo_find+ '"' + param + '":' + '"' + search_value +'"'
                mongo_find=mongo_find + ','
                logger.info(mongo_find)
           # mongo_find = mongo_find[-1]
            mongo_find = mongo_find + '\"tapis_deleted\":null}'
            #logger.info(mongo_find)
        except Exception as e:
                logger.debug(e)
                raise errors.ResourceError(msg=str(e))
    result = t.meta.listDocuments(_tapis_set_x_headers_from_service=True, db=conf.tenant[g.tenant_id]['stream_db'],collection='streams_project_metadata', filter= mongo_find )
    logger.info(result)
