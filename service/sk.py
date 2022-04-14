import enum
import requests
import json

from service import meta
from service import kapacitor

from flask import g, Flask
from tapisservice.tapisflask.utils import conf
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
def grant_role(role_name, username):
    logger.debug('granting role'+role_name+ 'in tenant'+g.tenant_id )
    try:
        grant_role_result = t.sk.grantRole(roleName= role_name, tenant= g.tenant_id, user = username)
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
    admin = 'streams_projects_'+ project_oid+"_admin"
    manager = 'streams_projects_'+ project_oid+"_manager"
    user = 'streams_projects_'+ project_oid+"_user"
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
    admin = 'streams_projects_'+ project_oid+"_admin"
    manager = 'streams_projects_'+ project_oid+"_manager"
    authorized = t.sk.hasRoleAny(tenant=g.tenant_id, user=g.username, roleNames=[admin, manager],
                                 orAdmin=False)
    logger.debug(authorized.isAuthorized)
    return authorized.isAuthorized

# User in any of the roles: Admin or Manager can perform PUT
def check_if_authorized_put(project_id):
    logger.debug(f'Checking if the user is authorized to update the resource')
    project_result, msg = meta.get_project(project_id)
    project_oid = project_result['_id']['$oid']
    admin = 'streams_projects_' + project_oid + "_admin"
    manager = 'streams_projects_' + project_oid + "_manager"
    authorized = t.sk.hasRoleAny(tenant=g.tenant_id, user=g.username, roleNames=[admin, manager],
                                 orAdmin=False)
    logger.debug(authorized)
    return authorized.isAuthorized

# Only the Admin can delete project
def check_if_authorized_delete(project_id):
    logger.debug(f'Checking if the user is authorized to delete the resource')
    project_result, msg = meta.get_project(project_id)
    project_oid = project_result['_id']['$oid']
    admin = 'streams_projects_' + project_oid + "_admin"
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
    admin = 'streams_channel_'+ channel_oid+"_admin"
    manager = 'streams_channel_'+ channel_oid+"_manager"
    user = 'streams_channel_'+ channel_oid+"_user"
    authorized = t.sk.hasRoleAny(tenant=g.tenant_id, user=g.username, roleNames=[admin, manager, user],
                                 orAdmin=False)
    logger.debug(authorized)
    return authorized.isAuthorized


def check_if_authorized_post_channel(channel_id):
    logger.debug(f'Checking if the user is authorized to create channel')
    channel_result,msg=kapacitor.get_channel(channel_id)
    channel_oid = channel_result['_id']['$oid']
    logger.debug(channel_oid)
    admin = 'streams_channel_'+ channel_oid+"_admin"
    manager = 'streams_channel_'+ channel_oid+"_manager"
    authorized = t.sk.hasRoleAny(tenant=g.tenant_id, user=g.username, roleNames=[admin, manager],
                                 orAdmin=False)
    logger.debug(authorized)
    return authorized.isAuthorized

def check_if_authorized_put_channel(channel_id):
    logger.debug(f'Checking if the user is authorized to update channel')
    channel_result,msg=kapacitor.get_channel(channel_id)
    channel_oid = channel_result['_id']['$oid']
    logger.debug(channel_oid)
    admin = 'streams_channel_'+ channel_oid+"_admin"
    manager = 'streams_channel_'+ channel_oid+"_manager"
    authorized = t.sk.hasRoleAny(tenant=g.tenant_id, user=g.username, roleNames=[admin, manager],
                                 orAdmin=False)
    logger.debug(authorized)
    return authorized.isAuthorized

def check_if_authorized_delete_channel(channel_id):
    logger.debug(f'Checking if the user is authorized to delete channel')
    channel_result,msg=kapacitor.get_channel(channel_id)
    channel_oid = channel_result['_id']['$oid']
    logger.debug(channel_oid)
    admin = 'streams_channel_'+ channel_oid+"_admin"
    authorized = t.sk.hasRoleAny(tenant=g.tenant_id, user=g.username, roleNames=[admin],
                                 orAdmin=False)
    logger.debug(authorized)
    return authorized.isAuthorized

# This function is used to get the roles of users associated with the resource id
# resource_type can only be project or channel
# jwt_user_flag is set to True to get the jwt user roles and set to false for user specified in the request body or query paramters
def check_user_has_role(username, resource_type, resource_id,jwt_user_flag):
    # Before the jwt user can check anyone's role on the project it is necessary that the jwt_user has some role on the project/channel
    logger.debug(f'Checking if the jwt user has any role on the project/channel')
    user_roles = []
    jwt_user_roles = []
    if (resource_type == 'project'):
        # call the metadata method to get the project_oid which is the mongo collection id
        project_result, msg = meta.get_project(resource_id)
        project_oid = project_result['_id']['$oid']
        logger.debug(project_oid)
        admin = 'streams_projects_' + project_oid + "_admin"
        manager = 'streams_projects_' + project_oid + "_manager"
        user = 'streams_projects_' + project_oid + "_user"

    elif (resource_type == 'channel'):
        # call the metadata method to get the channel_oid which is the mongo collection id
        channel_result, msg = kapacitor.get_channel(resource_id)
        channel_oid = channel_result['_id']['$oid']
        logger.debug(channel_oid)
        admin = 'streams_channel_' + channel_oid + "_admin"
        manager = 'streams_channel_' + channel_oid + "_manager"
        user = 'streams_channel_' + channel_oid + "_user"

    # If jwt_user_flag is false, we are getting roles for user specified in query paramters or request body
    # Before the jwt_user can access roles, we need to check if the jwt_user has any of the three roles on the resource_id
    if not jwt_user_flag:
        jwt_user_role = t.sk.hasRoleAny(tenant=g.tenant_id, user=g.username, roleNames=[admin, manager, user], orAdmin=False)
        logger.debug(jwt_user_role.isAuthorized)
        # jwt user has role on the resource id
        if(jwt_user_role.isAuthorized):
            # Check if the user in request body/query parameter has either of the three roles, if so append the rolenames to a list
            is_admin = t.sk.hasRole(tenant=g.tenant_id, user=username, roleName=admin,
                                 orAdmin=False)
            if(is_admin.isAuthorized):
                user_roles.append('admin')

            is_manager = t.sk.hasRole(tenant=g.tenant_id, user=username, roleName=manager,
                                 orAdmin=False)
            if(is_manager.isAuthorized):
               user_roles.append('manager')

            is_user = t.sk.hasRole(tenant=g.tenant_id, user=username, roleName=user,
                                  orAdmin=False)
            if (is_user.isAuthorized):
                user_roles.append('user')

            logger.debug(user_roles)
            # if the user_roles is not empty, that means roles are found for the user
            if user_roles:
                msg = f'Roles found'
            else:
                # no roles found for the user
                msg = f'Roles not found'
        else:
            # jwt user does not have any role on the resource, so they cannot access anyone's roles
            msg = f'User not authorized to access roles'
        return user_roles, msg
    # get the jwt user roles
    else:
        is_admin = t.sk.hasRole(tenant=g.tenant_id, user=g.username, roleName=admin,
                                orAdmin=False)
        logger.debug(is_admin)
        if (is_admin.isAuthorized):
           jwt_user_roles.append('admin')
           logger.debug(jwt_user_roles)
        is_manager = t.sk.hasRole(tenant=g.tenant_id, user=g.username, roleName=manager,
                                  orAdmin=False)
        logger.debug(is_admin)
        if (is_manager.isAuthorized):
            jwt_user_roles.append('manager')
            logger.debug(jwt_user_roles)
        is_user = t.sk.hasRole(tenant=g.tenant_id, user=g.username, roleName=user,
                               orAdmin=False)
        logger.debug(is_user)
        if (is_user.isAuthorized):
            jwt_user_roles.append('user')
            logger.debug(jwt_user_roles)
        if jwt_user_roles:
            msg = f'Roles found'
        else:
            msg = f'Roles not found'
        logger.debug(msg)
        return jwt_user_roles, msg



# this function is used to construct the role name that will be stored in sk depending on the resource type
def construct_role_name(resource_id,role_name, resource_type):
    logger.debug(f'Inside construct_role_name')
    if (resource_type == 'project'):
        project_result, msg = meta.get_project(resource_id)
        project_oid = project_result['_id']['$oid']
        logger.debug(project_oid)
        role_name = 'streams_projects_' + project_oid + "_"+role_name
    elif (resource_type == 'channel'):
        channel_result, msg = kapacitor.get_channel(resource_id)
        channel_oid = channel_result['_id']['$oid']
        logger.debug(channel_oid)
        role_name = 'streams_channel_' + channel_oid + "_"+ role_name
    else:
        msg = 'Invalid resource type'
        logger.debug(msg)
        raise errors.ResourceError(msg=f'Invalid resource type')
    logger.debug(role_name)
    return role_name

# This function is used to create and grant role to the user in the post request body
def grant_role_user_asking(resource_id,role_name, resource_type, username):
    description = f'Streams  ' + role_name + ' role'
    rolename_with_oid = construct_role_name(resource_id, role_name, resource_type)
    logger.debug(rolename_with_oid)
    role_created =create_role(rolename_with_oid, description)
    if (role_created == 'success'):
        role_granted = grant_role(rolename_with_oid, username)
        logger.debug(role_granted)
        if (role_granted == 'success'):
            msg = f'Role ' + role_name + f' successfully granted'
            logger.debug(msg)
            return role_name, msg
        else:
            msg = f'Role ' + role_name + f' not granted'
            return utils.error(result='', msg=msg)

    else:
        msg = f'Role not created'
        return utils.error(result='', msg=msg)

def delete_role_user_asking(resource_id,role_name, resource_type, username):
    rolename_with_oid = construct_role_name(resource_id, role_name, resource_type)
    logger.debug(rolename_with_oid)
    delete_role_sk = t.sk.revokeUserRole(roleName=rolename_with_oid, tenant=g.tenant_id, user=username)
    logger.debug(delete_role_sk)

    if ('1' in str(delete_role_sk)):
        msg = f'Role ' + role_name + f' successfully deleted for user ' + username
        logger.debug(msg)
        return role_name, msg
    else:
        msg = f'Role ' + role_name + f' not deleted for user ' + username
        logger.debug(msg)
        return utils.error(result='', msg=msg)

# User in any of the roles: Admin or Manager can perform PUT for Template
def check_if_authorized_put_template(template_id):
    logger.debug(f'Checking if the user is authorized to update the resource')
    template_result, msg = kapacitor.get_template(template_id)
    template_result = template_result['_id']['$oid']
    admin = 'streams_template_' + template_result + "_admin"
    manager = 'streams_template_' + template_result + "_manager"
    logger.debug(admin)
    logger.debug(manager)
    authorized = t.sk.hasRoleAny(tenant=g.tenant_id, user=g.username, roleNames=[admin, manager],
                                 orAdmin=False)
    logger.debug(authorized)
    return authorized.isAuthorized

