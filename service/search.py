from service import meta
import subprocess
from requests.auth import HTTPBasicAuth
from service import auth
from tapisservice.logs import get_logger
from tapisservice import errors
from tapisservice.tapisflask import utils
import requests
import json
import datetime
from flask import g, Flask
from tapisservice.config import conf
app = Flask(__name__)
# get the logger instance -
logger = get_logger(__name__)


t = auth.t


def args_parse(request, resource_type):
    logger.info(f'Inside args_parse')
    query = request.args.to_dict(flat=False)
    logger.info(f'Searching for: {query}')
    operators = ['neq', 'eq', 'lte', 'lt', 'gte', 'gt', 'nin', 'in']
    params = {
        'project': ['project_name', 'project_id', 'owner', 'pi', 'funding_resource', 'project_url', 'active', 'created_at', 'last_updated'],
        'site': ['site_name', 'site_id', 'owner', 'project_id', 'longitude', 'latitude', 'elevation', 'created_at', 'last_updated', 'metadata'],
        'instrument': ['inst_name', 'inst_id', 'inst_description', 'owner', 'site_id', 'project_id', 'created_at', 'last_updated', 'metadata'],
        'variable': ['var_name', 'var_id', 'owner', 'inst_id', 'shortname', 'unit', 'unit_abbrev', 'measured_property', 'created_at', 'last_updated', 'metadata']}
    # [(['project_id', 'in'], ['test']), (['owner', 'neq'], ['test1'])]
    search_list = [(k.split('.'), v) for k, v in query.items()]
    logger.info(search_list)
    constructed_query = []
    project_id_provided = -1
    # validation of search parameters
    for i in (0, len(search_list)-1):
        if(search_list[i][0][0] == 'project_id'):
            project_id_provided = i
        if(search_list[i][0][0] not in params[resource_type]):
            raise errors.ResourceError(
                msg=f'Invalid search parameter: {search_list[i][0][0]}.')
        if(search_list[i][0][1] not in operators):
            raise errors.ResourceError(
                msg=f'Invalid operator: {search_list[i][0][1]}.')
        constructed_query.append([search_list[i][0][0], search_list[i][0][1], str(
            search_list[i][1]).strip('[,\',]')])
    if(resource_type in ['site', 'instrument', 'variable'] and project_id_provided == -1):
        raise errors.ResourceError(
            msg=f'project_id is required when searching for site, instrument and variable.' )
    if(resource_type in ['site', 'instrument', 'variable'] and search_list[project_id_provided][0][1] != 'eq'):
        raise errors.ResourceError(
            msg=f'project_id must be paired with the eq operator when searching for site, instrument and variable.')
    #logger.info(f' query constructed ')
    return constructed_query


def build_mongo_search_query(mongo_find, param, operator, search_value):
    if(operator == 'eq'):
        mongo_find = mongo_find + '"' + param + '":' + '"' + search_value + '"'
    elif(operator == 'neq'):
        mongo_find = mongo_find + '"' + param + \
            '":' + '{$ne:' + search_value + '}}'
    elif(operator == 'lt'):
        mongo_find = mongo_find + '"' + param + \
            '":' + '{$lt:' + search_value + '}}'
    elif(operator == 'lte'):
        mongo_find = mongo_find + '"' + param + \
            '":' + '{$lte:' + search_value + '}}'
    elif(operator == 'gt'):
        mongo_find = mongo_find + '"' + param + \
            '":' + '{$gt:' + search_value + '}}'
    elif(operator == 'gte'):
        mongo_find = mongo_find + '"' + param + \
            '":' + '{$gte:' + search_value + '}}'
    elif(operator == 'in'):
        mongo_find = mongo_find + '"' + param + \
            '":' + '{$lt:' + search_value + '}}'
    # SQL LIKE Operator:
    # %: multi-character wildcard (replace % with .*)
    # _: single-character wildcard (replace _ with .)
    elif(operator == 'like'):
        mongo_find = mongo_find + '"' + param + \
            '":' + '{$regex:' + search_value + '}}'
    elif(operator == 'like'):
        mongo_find = mongo_find + '"' + param + '":' + \
            '{$not: {$regex:' + search_value + '}}}'
    logger.info(mongo_find)
    return mongo_find


# Example: curl -H "X-Tapis-Token:$jwt" http://localhost:5000/v3/streams/project?'project_id.eq=test_project2023-03-06T11:33:52.178730&owner=testuser2'
'''
 Possible search parameters are: project_name, project_id, owner, 
 pi, funding_resource, project_url, active, created_at, last_updated

'''


def project_search(request):
    logger.info(f'Inside project_search')
    args_list = args_parse(request, 'project')
    logger.info(args_list)
    #all_projects= meta.list_projects(100,0)
    # logger.info(all_projects)
   # project_data=json.dumps(all_projects[0])
    if (len(args_list) > 0):
        try:
            mongo_find = '{'
            for i in range(0, len(args_list)):
                param = args_list[i][0]
                operator = args_list[i][1]
                search_value = args_list[i][2]
                logger.info(
                    f'param: {param} operator: {operator} search_value: {search_value}')
                mongo_find = build_mongo_search_query(
                    mongo_find, param, operator, search_value)
                #mongo_find = mongo_find+ '"' + param + '":' + '"' + search_value +'"'
                mongo_find = mongo_find + ','
                logger.info(mongo_find)
           # mongo_find = mongo_find[-1]
            mongo_find = mongo_find + '\"tapis_deleted\":null}'
            # logger.info(mongo_find)
        except Exception as e:
            logger.debug(e)
            raise errors.ResourceError(msg=str(e))
    result = t.meta.listDocuments(_tapis_set_x_headers_from_service=True,
                                  db=conf.tenant[g.tenant_id]['stream_db'], collection='streams_project_metadata', filter=mongo_find)
    logger.info(result)

def site_search(request):
    logger.info(f'Inside site_search')
    args_list = args_parse(request, 'site')
    logger.info(args_list)
    project_id = ''
    #all_projects= meta.list_projects(100,0)
    # logger.info(all_projects)
   # project_data=json.dumps(all_projects[0])
    if (len(args_list) > 0):
        try:
            mongo_find = '{'
            for i in range(0, len(args_list)):
                param = args_list[i][0]
                operator = args_list[i][1]
                search_value = args_list[i][2]
                if param == 'project_id':
                    project_id = search_value
                logger.info(
                    f'param: {param} operator: {operator} search_value: {search_value}')
                mongo_find = build_mongo_search_query(
                    mongo_find, param, operator, search_value)
                #mongo_find = mongo_find+ '"' + param + '":' + '"' + search_value +'"'
                mongo_find = mongo_find + ','
                logger.info(mongo_find)
           # mongo_find = mongo_find[-1]
            mongo_find = mongo_find + '\"tapis_deleted\":null}'
            # logger.info(mongo_find)
        except Exception as e:
            logger.debug(e)
            raise errors.ResourceError(msg=str(e))
    result = t.meta.listDocuments(_tapis_set_x_headers_from_service=True,
                                  db=conf.tenant[g.tenant_id]['stream_db'], collection=project_id, filter=mongo_find)
    logger.info(result)

def instrument_search(request):
    logger.info(f'Inside instrument_search')
    args_list = args_parse(request, 'instrument')
    logger.info(args_list)
    project_id = ''
    #all_projects= meta.list_projects(100,0)
    # logger.info(all_projects)
   # project_data=json.dumps(all_projects[0])
    if (len(args_list) > 0):
        try:
            mongo_find = '{'
            for i in range(0, len(args_list)):
                param = args_list[i][0]
                operator = args_list[i][1]
                search_value = args_list[i][2]
                if param == 'project_id':
                    project_id = search_value
                logger.info(
                    f'param: {param} operator: {operator} search_value: {search_value}')
                mongo_find = build_mongo_search_query(
                    mongo_find, param, operator, search_value)
                #mongo_find = mongo_find+ '"' + param + '":' + '"' + search_value +'"'
                mongo_find = mongo_find + ','
                logger.info(mongo_find)
           # mongo_find = mongo_find[-1]
            mongo_find = mongo_find + '\"tapis_deleted\":null}'
            # logger.info(mongo_find)
        except Exception as e:
            logger.debug(e)
            raise errors.ResourceError(msg=str(e))
    result = t.meta.listDocuments(_tapis_set_x_headers_from_service=True,
                                  db=conf.tenant[g.tenant_id]['stream_db'], collection=project_id, filter=mongo_find)
    logger.info(result)

def variable_search(request):
    logger.info(f'Inside variable_search')
    args_list = args_parse(request, 'variable')
    logger.info(args_list)
    project_id = ''
    #all_projects= meta.list_projects(100,0)
    # logger.info(all_projects)
   # project_data=json.dumps(all_projects[0])
    if (len(args_list) > 0):
        try:
            mongo_find = '{'
            for i in range(0, len(args_list)):
                param = args_list[i][0]
                operator = args_list[i][1]
                search_value = args_list[i][2]

                if param == 'project_id':
                    project_id = search_value
                logger.info(
                    f'param: {param} operator: {operator} search_value: {search_value}')
                mongo_find = build_mongo_search_query(
                    mongo_find, param, operator, search_value)
                #mongo_find = mongo_find+ '"' + param + '":' + '"' + search_value +'"'
                mongo_find = mongo_find + ','
                logger.info(mongo_find)
           # mongo_find = mongo_find[-1]
            mongo_find = mongo_find + '\"tapis_deleted\":null}'
            # logger.info(mongo_find)
        except Exception as e:
            logger.debug(e)
            raise errors.ResourceError(msg=str(e))
    result = t.meta.listDocuments(_tapis_set_x_headers_from_service=True,
                                  db=conf.tenant[g.tenant_id]['stream_db'], collection=project_id, filter=mongo_find)
    logger.info(result)
