import requests
import json
from datetime import datetime
import re
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
    query.pop("skip", None)
    query.pop("limit", None)
    query.pop("computeTotal", None)
    query.pop("listType", None)
    search_list = [(k.split('.'), v) for k, v in query.items()]
    logger.info(search_list)
    logger.info(len(search_list))
    constructed_query = []
    project_id_provided = -1
    # validation of search parameters
    for i in range(len(search_list)):
        if(search_list[i][0][0] == 'project_id'):
            project_id_provided = i
        if(search_list[i][0][0] not in params[resource_type]):
                raise errors.ResourceError(msg=f'Invalid search parameter: {search_list[i][0][0]}.')
        if(search_list[i][0][1] not in operators):
                raise errors.ResourceError(msg=f'Invalid operator: {search_list[i][0][1]}.')
        constructed_query.append([search_list[i][0][0],search_list[i][0][1],str(search_list[i][1]).strip('[,\',]')])
    if(resource_type in ['site', 'instrument', 'variable'] and project_id_provided == -1):
        raise errors.ResourceError(
            msg=f'project_id is required when searching for site, instrument and variable.' )
    if(resource_type in ['site', 'instrument', 'variable'] and search_list[project_id_provided][0][1] != 'eq'):
        raise errors.ResourceError(
            msg=f'project_id must be paired with the eq operator when searching for site, instrument and variable.')
    #logger.info(f' query constructed ')
    return constructed_query

def build_mongo_search_query(mongo_find, param, operator,search_value):
    logger.info(search_value)
    multiple_search_values = search_value.split(",") 
    logger.info(len(multiple_search_values))
    if (len(multiple_search_values)>1):
        search_on=''
        for i in range (0, len(multiple_search_values)):
            logger.info(multiple_search_values[i])
            search_on= search_on+ "\'" + str(multiple_search_values[i]) + "\'" + ","
            logger.info(search_on)
        search_on=search_on[:-1]
    else:
        search_on=search_value
    logger.info(search_on)
    if(operator == 'eq'):
        mongo_find = mongo_find+ '"' + param + '":' + '"' + search_on +'"'
    elif(operator == 'neq'):
        mongo_find = mongo_find + '"' + param + \
            '":' + '{$ne:\'' + search_on + '\'}}'    
    elif(operator == 'in'):
        if(len(multiple_search_values) >1 ):
            mongo_find = mongo_find + '"' + param + \
            '":' + '{$in:[' + search_on + ']}}' 
        else:
            mongo_find = mongo_find + '"' + param + \
            '":' + '{$in:[\'' + search_on + '\']}}' 
    elif(operator == 'nin'):
        if(len(multiple_search_values) >1 ):
            mongo_find = mongo_find + '"' + param + \
            '":' + '{$nin:[' + search_on + ']}}' 
        else:
            mongo_find = mongo_find + '"' + param + \
            '":' + '{$nin:[\'' + search_on + '\']}}' 
    elif(operator == "gt"):
        isDate = False
        try:
            float(search_on)
        except Exception as e:
            logger.debug("Not a float, checking if its a date")
            try:
                datetime.strptime(str(search_on), "%Y-%m-%d")
            except Exception as e:
                logger.debug("Not a date: %s", str(e))
                raise Exception(f"Not a number or incorrect time string format (YYYY-mm-dd): {search_on}") from e
        if isDate:
            search_on += " 24:00:00.00000"

        mongo_find = mongo_find + '"' + param + \
        '":' + '{$gt:\"' + search_on + '\"}}'
    elif(operator == "gte"):
        try:
            float(search_on)
        except Exception as e:
            logger.debug("Not a float, checking if its a date")
            try:
                datetime.strptime(str(search_on), "%Y-%m-%d")
            except Exception as e:
                logger.debug("Not a date: %s", str(e))
                raise Exception(f"Not a number or incorrect time string format (YYYY-mm-dd): {search_on}") from e
        mongo_find = mongo_find + '"' + param + \
        '":' + '{$gte:\"' + search_on + '\"}}'
    elif(operator == "lt"):
        try:
            float(search_on)
        except Exception as e:
            logger.debug("Not a float, checking if its a date")
            try:
                datetime.strptime(str(search_on), "%Y-%m-%d")
            except Exception as e:
                logger.debug("Not a date: %s", str(e))
                raise Exception(f"Not a number or incorrect time string format (YYYY-mm-dd): {search_on}") from e
        
        mongo_find = mongo_find + '"' + param + \
        '":' + '{$lt:\"' + search_on + '\"}}'
    elif(operator == "lte"):
        isDate = False
        try:
            float(search_on)
        except Exception as e:
            logger.debug("Not a float, checking if its a date")
            try:
                datetime.strptime(str(search_on), "%Y-%m-%d")
                isDate = True
            except Exception as e:
                logger.debug("Not a date: %s", str(e))
                raise Exception(f"Not a number or incorrect time string format (YYYY-mm-dd): {search_on}") from e

        if isDate:
            search_on += " 24:00:00.00000"
        mongo_find = mongo_find + '"' + param + \
        '":' + '{$lte:\"' + search_on + '\"}}'
    logger.info(mongo_find)
    return mongo_find


#Example: curl -H "X-Tapis-Token:$jwt" http://localhost:5000/v3/streams/search/project?'project_id.eq=test_project2023-03-06T11:33:52.178730&owner.eq=testuser2'
'''
 Possible search parameters are: project_name, project_id, owner, 
 pi, funding_resource, project_url, active, created_at, last_updated

'''
def project_search(request, skip, limit):
    logger.info(f'Inside project_search')
    page = 1
    if skip >= 1000:
        page=skip/1000 + 1
        skip = skip - (page * 1000)
    if limit > 1000:
        raise errors.ResourceError(msg=f'Limit cannot exceed 1000')
    args_list = args_parse(request, "project")
    logger.info(args_list)
    if (len(args_list) > 0):
        try:
            mongo_find = '{'
            logger.info(len(args_list))
            for i in range(0,len(args_list)):
                param=args_list[i][0]
                operator=args_list[i][1]
                search_value=args_list[i][2]
                logger.info(f'param: {param} operator: {operator} search_value: {search_value}')
                mongo_find = build_mongo_search_query(mongo_find, param,operator,search_value )
                #mongo_find = mongo_find+ '"' + param + '":' + '"' + search_value +'"'
                mongo_find=mongo_find + ','
                logger.info(mongo_find)
           # mongo_find = mongo_find[-1]
            mongo_find = mongo_find + '\"permissions.users\": \"' + g.username + '\",\"tapis_deleted\":null}'
            logger.info(mongo_find)
        except Exception as e:
            logger.debug(e)
            raise errors.ResourceError(msg=str(e))
    result = t.meta.listDocuments(_tapis_set_x_headers_from_service=True, db=conf.tenant[g.tenant_id]['stream_db'],page=page, pagesize=1000, collection='streams_project_metadata', filter= mongo_find)
    logger.debug(result)
    sub_result=json.loads(result.decode('utf-8'))
    if len(sub_result) > 0:
        message = "Filtered Projects found"
        if skip + limit > 1000 and len(sub_result) == 1000:
            result2= t.meta.listDocuments(_tapis_set_x_headers_from_service=True, db=conf.tenant[g.tenant_id]['stream_db'],page=page+1,pagesize=1000, collection='streams_project_metadata',filter=mongo_find)
            sub_result.append(json.loads(result2.decode('utf-8')))
        try:
            logger.debug("skip: %d", skip)
            logger.debug("limit: %d", limit)
            if skip > 0:
                logger.debug('in skip')
                if limit > 0:
                    logger.debug('in limit')
                    end = int(skip)+int(limit)
                    sub_result = sub_result[int(skip):int(end)]
                else:
                    sub_result = sub_result[int(skip):-1]
            else:
                sub_result = sub_result[0:int(limit)]
            logger.debug('before return')
            logger.debug(sub_result)
            return sub_result, message
        except Exception as e:
            logger.debug(e)
            raise errors.ResourceError(msg=str(e))
    else:
        message = "No Projects found"
        logger.debug(result)
        return [], message
    #return sub_result
