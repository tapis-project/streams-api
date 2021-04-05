import enum
import requests
import json

from service import meta
from service import kapacitor

from flask import g, Flask
from common.config import conf
from common import auth
import datetime
app = Flask(__name__)

from common import utils, errors
from service import auth
# get the logger instance -
from common.logs import get_logger
logger = get_logger(__name__)

#pull out tenant from JWT
# t = DynaTapy(base_url=conf.tapis_base_url, username=conf.streams_user, service_password=conf.service_password, account_type=conf.streams_account_type, tenant_id='master')
# t.get_tokens()
t = auth.t

# Create role in SK
def create_role(role_name, description):
    logger.debug('creating role '+role_name+ ' in tenant '+ g.tenant_id)
    try:
        create_role_result,debug = t.sk.createRole(roleName=role_name, roleTenant=g.tenant_id, description='Streams role',_tapis_debug=True)
        logger.debug(debug)
        # If the result has string "url" we can confirm that role creation was success
        if ("url" in str(create_role_result)):
            logger.debug(f'Role created')
            return 'success'
        else:
            logger.debug(f"Role creation failed")
            return 'fail'
    except:
        raise errors.ResourceError(msg='Role creation failed: ' + role_name +' in tenant: '+ g.tenant_id)

# Grant role in SK
def grant_role(role_name):
    logger.debug('granting role'+role_name+ 'in tenant'+g.tenant_id )
    try:
        grant_role_result = t.sk.grantRole(roleName= role_name, tenant= g.tenant_id, user = g.username)
        # If the result has changes in the result grant role is successful
        # we can even call the sk.hasRole method to check this
        if ("changes" in str(grant_role_result)):
            logger.debug(f'Role granted')
            return 'success'
        else:
            logger.debug(f"Role grant failed")
            return 'fail'
    except:
        raise errors.ResourceError(msg='Role grant failed: ' + role_name +'in tenant: '+ g.tenant_id)


# Check if the user is authorized to do GET, PUT or DELETE req on Projects, Sites, Measurements, Variables, Instruments
# User in any of the roles: Admin, Manager, User can perform GET
def check_if_authorized_get(project_id):
    logger.debug(f'Checking if the user is authorized to get the resource details')
    project_result,msg=meta.get_project(project_id)
    #project_result = t.meta.getCollectionMetadata(db=conf.tenant[g.tenant_id]['stream_db'],collection=project_id)
    project_oid = project_result['_id']['$oid']
    logger.debug(project_oid)
    admin = 'streams_'+ project_oid+"_admin"
    manager = 'streams_'+ project_oid+"_manager"
    user = 'streams_'+ project_oid+"_user"
    authorized = t.sk.hasRoleAny(tenant=g.tenant_id, user=g.username, roleNames=[admin, manager, user],
                                 orAdmin=False)
    logger.debug(authorized)
    return authorized.isAuthorized

# User in any of the roles: Admin, Manager,can perform POST
def check_if_authorized_post(project_id):
    logger.debug(f'Checking if the user is authorized to create the resource')
    logger.debug(project_id)
    project_result,msg=meta.get_project(project_id)
    logger.debug(msg)
    project_oid = project_result['_id']['$oid']
    admin = 'streams_'+ project_oid+"_admin"
    manager = 'streams_'+ project_oid+"_manager"
    authorized = t.sk.hasRoleAny(tenant=g.tenant_id, user=g.username, roleNames=[admin, manager],
                                 orAdmin=False)
    logger.debug(authorized.isAuthorized)
    return authorized.isAuthorized

# User in any of the roles: Admin or Manager can perform PUT
def check_if_authorized_put(project_id):
    logger.debug(f'Checking if the user is authorized to update the resource')
    project_result, msg = meta.get_project(project_id)
    project_oid = project_result['_id']['$oid']
    admin = 'streams_' + project_oid + "_admin"
    manager = 'streams_' + project_oid + "_manager"
    authorized = t.sk.hasRoleAny(tenant=g.tenant_id, user=g.username, roleNames=[admin, manager],
                                 orAdmin=False)
    logger.debug(authorized)
    return authorized.isAuthorized

# Only the Admin can delete project
def check_if_authorized_delete(project_id):
    logger.debug(f'Checking if the user is authorized to delete the resource')
    project_result, msg = meta.get_project(project_id)
    project_oid = project_result['_id']['$oid']
    admin = 'streams_' + project_oid + "_admin"
    authorized = t.sk.hasRoleAny(tenant=g.tenant_id, user=g.username, roleNames=[admin],
                                 orAdmin=False)
    logger.debug(authorized)
    return authorized.isAuthorized

# Check if user is authorized to do GET, POST, PUT, DELETE on channels
def check_if_authorized_get_channel(channel_id):
    logger.debug(f'Checking if the user is authorized to get channel details')
    channel_result,msg=kapacitor.get_channel(channel_id)
    channel_oid = channel_result['_id']['$oid']
    logger.debug(channel_oid)
    admin = 'channel_'+ channel_oid+"_admin"
    manager = 'channel_'+ channel_oid+"_manager"
    user = 'channel_'+ channel_oid+"_user"
    authorized = t.sk.hasRoleAny(tenant=g.tenant_id, user=g.username, roleNames=[admin, manager, user],
                                 orAdmin=False)
    logger.debug(authorized)
    return authorized.isAuthorized


def check_if_authorized_post_channel(channel_id):
    logger.debug(f'Checking if the user is authorized to create channel')
    channel_result,msg=kapacitor.get_channel(channel_id)
    channel_oid = channel_result['_id']['$oid']
    logger.debug(channel_oid)
    admin = 'channel_'+ channel_oid+"_admin"
    manager = 'channel_'+ channel_oid+"_manager"
    authorized = t.sk.hasRoleAny(tenant=g.tenant_id, user=g.username, roleNames=[admin, manager],
                                 orAdmin=False)
    logger.debug(authorized)
    return authorized.isAuthorized

def check_if_authorized_put_channel(channel_id):
    logger.debug(f'Checking if the user is authorized to update channel')
    channel_result,msg=kapacitor.get_channel(channel_id)
    channel_oid = channel_result['_id']['$oid']
    logger.debug(channel_oid)
    admin = 'channel_'+ channel_oid+"_admin"
    manager = 'channel_'+ channel_oid+"_manager"
    authorized = t.sk.hasRoleAny(tenant=g.tenant_id, user=g.username, roleNames=[admin, manager],
                                 orAdmin=False)
    logger.debug(authorized)
    return authorized.isAuthorized

def check_if_authorized_delete_channel(channel_id):
    logger.debug(f'Checking if the user is authorized to delete channel')
    channel_result,msg=kapacitor.get_channel(channel_id)
    channel_oid = channel_result['_id']['$oid']
    logger.debug(channel_oid)
    admin = 'channel_'+ channel_oid+"_admin"
    authorized = t.sk.hasRoleAny(tenant=g.tenant_id, user=g.username, roleNames=[admin],
                                 orAdmin=False)
    logger.debug(authorized)
    return authorized.isAuthorized

def check_user_has_role(username, resource_type, resource_id):
    # Before the jwt user can check anyone's role on the project it is necessary that the user has some role on the project
    logger.debug(f'Checking if the jwt user has any role on the project')
    roles = []
    if (resource_type == 'project'):
        project_result, msg = meta.get_project(resource_id)
        project_oid = project_result['_id']['$oid']
        logger.debug(project_oid)
        admin = 'streams_' + project_oid + "_admin"
        manager = 'streams_' + project_oid + "_manager"
        user = 'streams_' + project_oid + "_user"

    elif (resource_type == 'channel'):
        channel_result, msg = kapacitor.get_channel(resource_id)
        channel_oid = channel_result['_id']['$oid']
        logger.debug(channel_oid)
        admin = 'channel_' + channel_oid + "_admin"
        manager = 'channel_' + channel_oid + "_manager"
        user = 'channel_' + channel_oid + "_user"

    # Check if the jwt user has any role on the project
    # if true, check for the user in the request args for roles
    jwt_user_role = t.sk.hasRoleAny(tenant=g.tenant_id, user=g.username, roleNames=[admin, manager, user],
                                 orAdmin=False)

    
    logger.debug(jwt_user_role.isAuthorized)
    if(jwt_user_role.isAuthorized):
        #req_user_role = t.sk.hasRole(tenant=g.tenant_id, user=username, roleNames=[admin],
                              #    orAdmin=False)
        #return req_user_role.isAuthorized
        req_user_role = t.sk.getUserRoles(tenant=g.tenant_id, user=username)
       # roles = req_user_role.names[]
        if admin in req_user_role.names:
            roles.append(admin)
        if manager in req_user_role.names:
            roles.append(manager)
        if user in req_user_role.names:
            roles.append(user)
        logger.debug(roles)
        if roles:
            msg = f'Roles found'
        else:
            msg = f'No roles found'
    else:
        msg = f'User not authorized to access roles'
    return roles, msg
