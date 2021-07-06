import datetime
import requests
import json
import pandas as pd
import sys

from flask import g, request, make_response
from flask_restful import Resource
from openapi_core.shortcuts import RequestValidator
from openapi_core.wrappers.flask import FlaskOpenAPIRequest

# import psycopg2
#import sqlalchemy
from service import chords
from service import influx
from service import meta
from service import kapacitor
from service import abaco
from service import sk
from service.models import ChordsSite, ChordsIntrument, ChordsVariable
from common import utils, errors
from common.config import conf
from requests.auth import HTTPBasicAuth
from common import errors as common_errors
from service import auth
from datetime import datetime

# get the logger instance -
from common.logs import get_logger
logger = get_logger(__name__)

# Hello resource: GET
class HelloResource(Resource):
    # GET v3/streams/hello
    def get(self):
        logger.debug(f"In hello resource")
        return utils.ok(result='',msg="Hello from Streams")

# Ready resource: GET
class ReadyResource(Resource):
    # GET v3/streams/ready
    def get(self):
        try:
            # Ping Kapacitor
            status_kapacitor=kapacitor.ping()
            logger.debug(f'Kapacitor status: '+str(status_kapacitor))

            # Ping Chords
            status_chords=chords.ping()
            logger.debug(f'Check Chords status: '+str(status_chords))

            # Ping InfluxDB
            status_influx = influx.ping()
            logger.debug(f'Check Influx status: '+str(status_influx))

            # Check if the all pings returned success, if so the streams service is ready otherwise not ready
            if(status_kapacitor == 204 and status_chords == 200 and status_influx == 204):
                return utils.ok(result='', msg=f'Streams Service ready')
        except:
            raise errors.ResourceError(msg=f'Streams Service not ready')

# Healthcheck resource: GET
class HealthcheckResource(Resource):
    # GET v3/streams/healthchceck?tenant=tenant.id
    # This is similar to ready except it checks the readiness of meta service
    def get(self):
        try:
            # Ping Kapacitor
            status_kapacitor = kapacitor.ping()
            logger.debug(f' Check Kapacitor status:'+str(status_kapacitor))
        except:
            # If Kapacitor is not ready raise resource error
            raise errors.ResourceError(msg=f'Kapacitor not ready')
        try:
            # Ping Chords
            status_chords = chords.ping()
            logger.debug(f'Check Chords status: '+str(status_chords))
        except:
            # If Chords is not ready raise resource error
            raise errors.ResourceError(msg=f'Chords not ready')
        try:
            # Ping InfluxDB
            status_influx = influx.ping()
            logger.debug(f'Check Influx status: '+str(status_influx))
        except:
            # If InfluxDB is not ready raise resource error
            raise errors.ResourceError(msg=f'Influx DB not ready')
        try:
            # Call meta service's healthcheck method
            status_meta = meta.healthcheck()
            logger.debug(f'Check Meta status: '+str(status_meta))
        except:
            # If meta service is not ready raise resource error
            raise errors.ResourceError(msg=f'Metadata not ready')
        # If all 4 services Kapacitor, Chords, InfluxDB and Meta is ready, Streams service is in good health
        return utils.ok(result='',msg="Streams in good health")

# Projects resource : LIST, CREATE
class ProjectsResource(Resource):
    """
    Work with Project objects
    """
    # Get project listings: GET v3/streams/projects
    def get(self):
            logger.debug(f'In list projects')
            proj_result, msg = meta.list_projects()
            result = meta.strip_meta_list(proj_result)
            logger.debug(f'After list projects')
            return utils.ok(result=result,msg=msg)

    # Create project: POST v3/streams/projects
    def post(self):
        logger.debug(f'In create projects')
        logger.debug(f'Request body: '+str(request.json))
        body = request.json
        req_body = body
        # Project creator will be assigned project admin role in SK.
        try:
            proj_result, msg = meta.create_project(body)
            logger.debug(f'Project Creation result from Meta'+str(proj_result))
            # Every project admin role has a fixed format stream_ + proj_result['_id']['$oid'] + _admin
            proj_admin_role = 'streams_projects_' + proj_result['_id']['$oid'] + '_admin'
            logger.debug(f'Project Admin role to be created in SK: '+ str(proj_admin_role))
            # Create role in SK. Only when the role creation is successful then grant it to the user.
            create_role_status = sk.create_role(proj_admin_role, 'Project Admin Role')
            if (create_role_status == 'success'):
               grant_role_status = sk.grant_role(proj_admin_role,g.username)
               # Check if the role was granted successfully to the user
               if (grant_role_status == 'success'):
                   # Only if the role is granted to user, call metadata service to create project collection
                   if (str(proj_result) != 'null'):
                    result = meta.strip_meta(proj_result)
                    return utils.ok(result, msg=msg)
               # If role granting was not success, we should cleanup the role from sk
               else:
                   try:
                     delete_role_sk = sk.deleteRoleByName(roleName=proj_admin_role,tenant=g.tenant_id)
                     logger.debug(f'Proj admin role deleted from SK: '+str(proj_admin_role))
                     msg = f"Could not create project"
                     return utils.error(result='null', msg=msg)
                   except Exception as e:
                       msg = f"Cound not delete role: {proj_admin_role};"
                       return utils.error(result='null', msg=msg)
            else:
                msg = f"Could not create project"
                return utils.error(result='null', msg=msg)
        except Exception as e:
              msg = f"Could not create project"
              return utils.error(result='null', msg=msg)
        return utils.error(result='null', msg=msg)

# Projects Resource: GET, UPDATE, DELETE
class ProjectResource(Resource):
    """
    Work with Project objects
    """
    # Get the project details: GET v3/streams/projects/{project_id}
    def get(self, project_id):
        logger.debug(f'In get project details')
        # Check if the user is authorized to access the project by checking the user has project specific role in sk
        authorized = sk.check_if_authorized_get(project_id)
        # Only if the user is authorized give the project details back in the response
        if(authorized):
            logger.debug(f'User is authorized to access project : '+str(project_id))
            proj_result, msg = meta.get_project(project_id)
            result = meta.strip_meta(proj_result)
            logger.debug(f' Get Project object from meta' +str(result))
            return utils.ok(result=result, msg=msg)
        else:
            logger.debug(f'User does not have any role on the project: '+ str(project_id))
            raise common_errors.PermissionsError(msg=f'User not authorized to access the resource')

    # Update the project: PUT v3/streams/projects/{project_id}
    def put(self, project_id):
        logger.debug(f'In update project')
        # Check if the user is authorized to access the project by checking the user has project specific role in sk
        authorized = sk.check_if_authorized_put(project_id)
        if (authorized):
            logger.debug(f'User is authorized to update project : '+str(project_id))
            body = request.json
            proj_result, msg = meta.update_project(project_id, body)
            result = meta.strip_meta(proj_result)
            return utils.ok(result=result, msg=msg)
        else:
            logger.debug(f'User does not have Admin or Manager role on the project: '+ str(project_id))
            raise common_errors.PermissionsError(msg=f'User not authorized to access the resource')

    # Delete the project DELETE v3/streams/projects/{project_id}
    def delete(self, project_id):
        logger.debug(f'In delete project')
        # Check if the user is authorized to access the project by checking the user has project specific role in sk

        authorized = sk.check_if_authorized_delete(project_id)
        if (authorized):
             logger.debug(f'User is authorized to delete project : ' + str(project_id))
             proj_result, msg = meta.delete_project(project_id)
             result = meta.strip_meta(proj_result)
             return utils.ok(result=result, msg=msg)
        else:
            logger.debug(f'User does not have Admin role on the project: '+ str(project_id))
            raise common_errors.PermissionsError(msg=f'User not authorized to access the resource')

# Site Resource: LIST, CREATE
class SitesResource(Resource):
    """
    Work with Sites objects
    """
    # Get site listings: GET v3/streams/projects/{project_id}/sites
    #TODO metadata integration - need to use query, limit and offset
    def get(self, project_id):
        logger.debug(f'In list sites')
        # Check if the user is authorized to access the site by checking if the user has project specific role
        authorized = sk.check_if_authorized_get(project_id)
        logger.debug(f'Authorization status: '+ str(authorized))
        if (authorized):
            logger.debug(f'User is authorized to list sites for project : ' + str(project_id))
            site_result, msg = meta.list_sites(project_id)
            result = meta.strip_meta_list(site_result)
            return utils.ok(result=result,msg=msg)
        else:
            logger.debug(f'Authorization failed. User does not have role any role on the project')
            raise common_errors.PermissionsError(msg=f'User not authorized to access the resource')

    # Create Site: POST v3/streams/projects/{project_id}/sites
    def post(self, project_id):
        logger.debug(f'In create sites')
        # Check if the user is authorized to create the site by checking if the user has project specific role

        authorized = sk.check_if_authorized_post(project_id)
        logger.debug(authorized)
        if (authorized):
                logger.debug(f'User is authorized to create sites for project : ' + str(project_id))
                logger.debug(f'Request body'+ str(request.json))
                body = request.json
                postSite = ChordsSite("",body['site_name'],
                                        body['latitude'],
                                        body['longitude'],
                                        body['elevation'],
                                        body['description'])
                # Create chords site
                resp, msg = chords.create_site(postSite)
                # If site is successfully created in chords create a document in MongoDB
                if msg == "Site created":
                    site_result, message = meta.create_site(project_id, resp['id'],body)
                    #resp['results']=meta_resp['results']
                    logger.debug(f'Metadata site creation success')
                    logger.debug(f'Site object' +str(site_result))
                    # Remove the _id and _etag for a list of metadata objects

                    result = meta.strip_meta(site_result)
                else:
                    logger.debug(f'Metadata site creation failed')
                    message = msg
                    result=''
                return utils.ok(result=result,msg=message)
        else:
            logger.debug(f'User does not have Admin or Manager role on the project')
            raise common_errors.PermissionsError(msg=f'User not authorized to access the resource')

# Site Resource: GET, UPDATE, DELETE
class SiteResource(Resource):
    """
    Work with Sites objects
    """
    # Get site details: GET v3/streams/projects/{project_id}/sites/{site_id}
    def get(self, project_id, site_id):
        logger.debug(f'In get site details')
        # Check if the user is authorized to get the site details by checking if the user has project specific role
        authorized = sk.check_if_authorized_get(project_id)
        if(authorized):
            logger.debug(f'User is authorized to get sites details : ' + str(site_id))
            # Get site details from metadata
            site_result, msg = meta.get_site(project_id,site_id)
            # Remove the _id and _etag for a list of metadata objects
            result = meta.strip_meta(site_result)
            logger.debug(f'Site object'+str(result))
            return utils.ok(result=result, msg=msg)
        else:
            logger.debug(f'User does not have any role on project')
            raise common_errors.PermissionsError(msg=f'User not authorized to access the resource')

    # Update site PUT v3/streams/projects/{project_id}/sites/{site_id}
    def put(self, project_id, site_id):
        logger.debug(f'In update site ')
        # Check if the user is authorized to update the site  by checking if the user has project specific role
        authorized = sk.check_if_authorized_put(project_id)
        if (authorized):
            logger.debug(f'User is authorized to update site : ' + str(site_id))
            body = request.json
            # Update site metadata in MongoDB
            site_result, msg = meta.update_site(project_id, site_id, body)
            # Remove the _id and _etag for a list of metadata objects
            result = meta.strip_meta(site_result)
            # Request body for update
            putSite = ChordsSite(result['chords_id'],
                                  body['site_name'],
                                  body['latitude'],
                                  body['longitude'],
                                  body['elevation'],
                                  body['description'])
            # Update site metadata in Chords
            chord_result, chord_msg = chords.update_site(result['chords_id'], putSite)
            return utils.ok(result=result, msg=msg)
        else:
            logger.debug(f'User does not have Admin or Manager role on the project')
            raise common_errors.PermissionsError(msg=f'User not authorized to access the resource')

    # Delete Site: DELETE  v3/streams/projects/{project_id}/sites/{site_id}
    def delete(self, project_id, site_id):
        logger.debug(f'In delete site ')
        # Check if the user is authorized to delete the site  by checking if the user has project specific role
        authorized = sk.check_if_authorized_delete(project_id)
        if (authorized):
            logger.debug(f'User is authorized to delete site : ' + str(site_id))
            #result, msg = chords.delete_site(site_id)
            # Update site metadata in MongoDB

            site_result, msg = meta.delete_site(project_id,site_id)
            logger.debug(msg)
            return utils.ok(result=site_result, msg=f'Site {site_id} deleted.')
        else:
            logger.debug(f'User does not have Admin role on the project')
            raise common_errors.PermissionsError(msg=f'User not authorized to access the resource')

# Instrument resources: LIST, CREATE
class InstrumentsResource(Resource):
    """
    Work with Instruments objects
    """
    # Get Instrument listings: GET v3/streams/projects/{project_id}/sites/{site_id}/instruments
    def get(self,project_id,site_id):
        logger.debug(f'In list instruments')
        # Check if the user is authorized to list instruments  by checking if the user has project specific role
        authorized = sk.check_if_authorized_get(project_id)
        if (authorized):
            logger.debug(f'User is authorized to list instruments for site : ' + str(site_id))
            # List instruments for a given project and site id
            result,msg = meta.list_instruments(project_id, site_id)
            logger.debug(f'Site id' +str(site_id))
            '''
            #logic to filter instruments based on site id
            filtered_res = []
            list_index = 0
            logger.debug(site_id)
            for i in range(len(result)):
                if (result[i]["site_id"] == int(site_id)):
                    filtered_res.insert(list_index, result[i])
                    list_index = list_index + 1
                    logger.debug(filtered_res)
                if (len(filtered_res)!=0):
                    return utils.ok(result=filtered_res, msg=msg)
                else:
                    return utils.ok(result="null", msg=f'No instruments found with this site')
            '''
            return utils.ok(result=result, msg=msg)
        else:
            logger.debug(f'User does not have any role on project')
            raise common_errors.PermissionsError(msg=f'User not authorized to access the resource')

    # Create instruments POST v3/streams/projects/{project_id}/sites/{site_id}/instruments
    #TODO support bulk create operations
    def post(self, project_id, site_id):
        logger.debug(f'In create instruments')
        # Check if the user is authorized to create instruments  by checking if the user has project specific role
        authorized = sk.check_if_authorized_post(project_id)
        if (authorized):
            logger.debug(f'User is authorized to create instruments for site : ' + str(site_id))
            #logger.debug(type(request.json))
            logger.debug(f'Request body' +str(request.json))
            result={}
            #TODO loop through list objects to support build operations
            if type(request.json) is dict:
                body = request.json
            else:
                body = request.json[0]
            logger.debug(f'before ChordsInstrument assignment')
            #id, site_id, name, sensor_id, topic_category_id, description, display_points, plot_offset_value, plot_offset_units, sample_rate_seconds):
            site_result, site_bug = meta.get_site(project_id, site_id)
            if site_bug == "Site found.":
                postInst = ChordsIntrument("",site_result['chords_id'],
                                            body['inst_name'],
                                            "",
                                            "",
                                            body['inst_description'],
                                            "120",
                                            "1",
                                            "weeks",
                                            "60")
                logger.debug(f'after ChordsInstrument assignment')
                # Create instrument in chords
                chord_result, chord_msg = chords.create_instrument(postInst)
                logger.debug(chord_msg)
                if chord_msg == "Instrument created":
                    body['chords_id'] = chord_result['id']
                    # create instrument document in MongoDB
                    inst_result, inst_msg = meta.create_instrument(project_id, site_id, body)
                    logger.debug(f'Instrument result'+str(inst_msg))
                    if len(inst_result) >0:
                        result = inst_result
                        message = inst_msg
                else:
                    logger.debug(f'Instrument not created in chords due to ' +str(chord_msg))
                    message = chord_msg
            else:
                logger.debug(f"INSTRUMENT FAILED TO CREATE")
                message = "Instrument Failed To Create"
            return utils.ok(result=result, msg=message)
        else:
            logger.debug(f'User does not have Admin or Manager role on project')
            raise common_errors.PermissionsError(msg=f'User not authorized to access the resource')

# Instrument resources: GET, UPDATE, DELETE
class InstrumentResource(Resource):
    """
    Work with Instruments objects
    """
    # Get Instrument details: GET v3/streams/projects/{project_id}/sites/{site_id}/instruments/{instrument_id}
    def get(self, project_id, site_id, instrument_id):
        logger.debug(f'In get instruments')
        # Check if the user is authorized to get instrument details by checking if the user has project specific role
        authorized = sk.check_if_authorized_get(project_id)
        if (authorized):
            logger.debug(f'User is authorized to get instrument details for : ' + str(instrument_id))
            # Get instrument metadata with metadata service
            result,msg = meta.get_instrument(project_id, site_id,instrument_id)
            return utils.ok(result=result, msg=msg)
        else:
            logger.debug(f'User does not have any role on project')
            raise common_errors.PermissionsError(msg=f'User not authorized to access the resource')

    # Update Instrument: PUT v3/streams/projects/{project_id}/sites/{site_id}/instruments/{instrument_id}
    def put(self, project_id, site_id, instrument_id):
        logger.debug(f'In update instruments')
        # Check if the user is authorized to update instrument details by checking if the user has project specific role
        authorized = sk.check_if_authorized_put(project_id)
        if (authorized):
            logger.debug(f'User is authorized to update instrument details for : ' + str(instrument_id))
            logger.debug(type(request.json))
            logger.debug(f'Request body'+str(request.json))
            #TODO loop through list objects to support buld operations
            if type(request.json) is dict:
                body = request.json
            else:
                body = request.json[0]
            # Update instrument metadata
            result, msg = meta.update_instrument(project_id, site_id, instrument_id, body)
            putInst = ChordsIntrument(int(result['chords_id']),result['site_chords_id'],
                                        body['inst_name'],
                                        "",
                                        "",
                                        body['inst_description'],
                                        "",
                                        "",
                                        "",
                                        "")
            # Update instrument in chords
            chord_result, chord_msg = chords.update_instrument(str(result['chords_id']), putInst)
            return utils.ok(result=result, msg=msg)
        else:
            logger.debug(f'User does not have Admin or Manager role on the project')
            raise common_errors.PermissionsError(msg=f'User not authorized to access the resource')

    # Delete Instrument: DELETE v3/streams/projects/{project_id}/sites/{site_id}/instruments/{instrument_id}
    def delete(self, project_id, site_id, instrument_id):
        logger.debug(f'In delete instruments')
        # Check if the user is authorized to delete instrument details by checking if the user has project specific role
        authorized = sk.check_if_authorized_delete(project_id)
        if (authorized):
            logger.debug(f'User is authorized to delete instrument details for : ' + str(instrument_id))
            #chord_result,chord_msg = chords.delete_instrument(instrument_id)
            result, msg = meta.update_instrument(project_id, site_id, instrument_id, {},True)
            return utils.ok(result={}, msg=msg)
        else:
            logger.debug(f'User does not have admin role on the project')
            raise common_errors.PermissionsError(msg=f'User not authorized to access the resource')

# Variables resources: LIST, CREATE
class VariablesResource(Resource):
    """
    Work with Variables objects
    """
    # List variables: GET v3/streams/projects/{project_id}/sites/{site_id}/instruments/{instrument_id}/variables
    def get(self, project_id, site_id, instrument_id):
        logger.debug(f'In list variables')
        # Check if the user is authorized to list variables by checking if the user has project specific role
        authorized = sk.check_if_authorized_get(project_id)
        if (authorized):
            #result,msg = chords.list_variables()
            logger.debug(f'User is authorized to list variables for : ' + str(instrument_id))
            # List instruments
            result, msg = meta.list_variables(project_id, site_id, instrument_id)
            logger.debug(instrument_id)
            return utils.ok(result=result, msg=msg)
        else:
            logger.debug(f'User does not have any role on project')
            raise common_errors.PermissionsError(msg=f'User not authorized to access the resource')

    # Create variables: POST v3/streams/projects/{project_id}/sites/{site_id}/instruments/{instrument_id}/variables
    def post(self, project_id, site_id, instrument_id):
        logger.debug(f'In create variables')
        # Check if the user is authorized to create variables by checking if the user has project specific role

        authorized = sk.check_if_authorized_post(project_id)
        if (authorized):
            logger.debug(f'User is authorized to create variables for : ' + str(instrument_id))
            logger.debug(f' Request body' +str(request.json))
            #TODO loop through list objects to support buld operations
            if type(request.json) is dict:
                body = request.json
            else:
                body = request.json[0]
            inst_result, bug = meta.get_instrument(project_id, site_id, instrument_id)
            # id, name, instrument_id, shortname, commit
            postInst = ChordsVariable("test",inst_result['chords_id'],
                                        body['var_name'],
                                        body['var_id'],
                                        "")
            logger.debug(postInst)
            # Create variable in chords
            chord_result, chord_msg = chords.create_variable(postInst)
            if chord_msg == "Variable created":
                body['chords_id'] = chord_result['id']
                # Create a variable in mongo
                result, msg = meta.create_variable(project_id, site_id, instrument_id, body)
            else:
                message = chord_msg
                logger.debug(f' Chords variable not created due to '+ str(message))
            logger.debug(f' Variable creation meta result: ' + str(result))
            return utils.ok(result=result, msg=msg)
        else:
            logger.debug(f'User does not have admin or manager role on project')
            raise common_errors.PermissionsError(msg=f'User not authorized to access the resource')

# Variables resources: GET, UPDATE, DELETE
class VariableResource(Resource):
    """
    Work with Variables objects
    """
    # GET variable details: GET v3/streams/projects/{project_id}/sites/{site_id}/instruments/{instrument_id}/variables/{variable_id}
    def get(self, project_id, site_id, instrument_id, variable_id):
        logger.debug(f'In get variable details')
        # Check if the user is authorized to get variable details by checking if the user has project specific role
        authorized = sk.check_if_authorized_get(project_id)
        if (authorized):
            logger.debug(f'User is authorized to get variables details for variable : ' + str(variable_id))
            #chords_result,chords_msg = chords.get_variable(variable_id)
            # Get variable metadata
            result, msg = meta.get_variable(project_id, site_id, instrument_id, variable_id)
            logger.debug(f'Variable result' +str(result))
            return utils.ok(result=result, msg=msg)
        else:
            logger.debug(f'User does not have any role on project')
            raise common_errors.PermissionsError(msg=f'User not authorized to access the resource')

    # Update variables: PUT v3/streams/projects/{project_id}/sites/{site_id}/instruments/{instrument_id}/variables/{variable_id}
    def put(self,project_id, site_id, instrument_id,  variable_id):
        logger.debug(f'In update variable')
        # Check if the user is authorized to update variable  by checking if the user has project specific role
        authorized = sk.check_if_authorized_put(project_id)
        if (authorized):
            logger.debug(f'User is authorized to update variables details for variable : ' + str(variable_id))
            logger.debug(type(request.json))
            logger.debug(f'Request body' +str(request.json))
            #TODO loop through list objects to support buld operations
            if type(request.json) is dict:
                body = request.json
            else:
                body = request.json[0]
            result, msg = meta.update_variable(project_id, site_id, instrument_id, variable_id, body)
            putInst = ChordsVariable(result['chords_id'],result['inst_chords_id'],
                                        body['var_name'],
                                        body['shortname'],
                                        "")
            logger.debug(putInst)
            # Update variabel in chords
            chord_result,chord_msg = chords.update_variable(result['chords_id'],putInst)
            logger.debug(f'Update variable result meta' + str(result))
            return utils.ok(result=result, msg=msg)
        else:
            logger.debug(f'User does not have admin or manager role on project')
            raise common_errors.PermissionsError(msg=f'User not authorized to access the resource')

    # Delete variables: DELETE v3/streams/projects/{project_id}/sites/{site_id}/instruments/{instrument_id}/variables/{variable_id}
    def delete(self, project_id, site_id, instrument_id, variable_id):
        logger.debug(f'In delete variable')
        # Check if the user is authorized to delete variable  by checking if the user has project specific role
        authorized = sk.check_if_authorized_delete(project_id)
        if (authorized):
            logger.debug(f'User is authorized to delete variables details for variable : ' + str(variable_id))
            # Delete Variable in chords
            result,msg = chords.delete_variable(variable_id)
            result, msg = meta.update_variable(project_id, site_id, instrument_id, variable_id, {},True)
            logger.debug(f'Metadata delete variable result ' +str(result))
            return utils.ok(result=result, msg=msg)
        else:
            logger.debug(f'User does not have admin role on project')
            raise common_errors.PermissionsError(msg=f'User not authorized to access the resource')

# Measurements resources
class MeasurementsWriteResource(Resource):
    #at the moment expects some like
    #http://localhost:5000/v3/streams/measurements
    #will need to adjust when openAPI def is final for measurement
    def post(self):
        logger.debug('Inside post measurements')
        body = request.json
        logger.debug(f'Request body' +str(body))
        instrument = {}
        logger.debug(f"CONTENT_LENGTH: " + str(request.headers['content_length']))
        #logger.debug("Bytes:" + str(sys.getsizeof(body)))
        message = "Measurement Write Failed"
        if 'inst_id' in body:
            logger.debug('inst_id in body')
            result = meta.fetch_instrument_index(body['inst_id'])
            logger.debug(result)
            if len(result) > 0:
                logger.debug(result['chords_inst_id'])
                site_result, site_msg = meta.get_site(result['project_id'],result['site_id'])
                if 'instruments' in site_result:
                    for inst in site_result['instruments']:
                        if inst['inst_id'] == body['inst_id']:
                            instrument = inst
                    logger.debug(f' Site resu;t' +str(site_result))
                    project_id=result['project_id']
                    logger.debug(project_id)
                    # Check if the user is authoried to post measurements
                    authorized = sk.check_if_authorized_post(project_id)
                    logger.debug(f'Authorization status' +str(authorized))
                    if (authorized):
                        logger.debug(f' User is authorized to create measurements')
                        resp = influx.compact_write_measurements(site_result['chords_id'],instrument,body)
                        logger.debug(resp)
                        if resp['resp']:
                            metric = {'created_at':datetime.now().isoformat(),'type':'upload','project_id':result['project_id'],'username':g.username,'size':request.headers['content_length'],'var_count':len(body['vars'])}
                            metric_result, metric_bug =auth.t.meta.createDocument(db=conf.tenant[g.tenant_id]['stream_db'], collection='streams_metrics', request_body=metric, _tapis_debug=True)
                            logger.debug(metric_result)
                            return utils.ok(result=resp['body'], msg="Measurements Saved")
                        else:
                            raise common_errors.PermissionsError(msg=resp['msg']+ ' Measurement Failed to Save!')
                    else:
                        logger.debug(f'User does not have admin or manager role on project')
                        raise common_errors.PermissionsError(msg=f'User not authorized to access the resource')

                logger.debug(f' Influx response: ' +str(resp))
            else:
                raise errors.ResourceError(msg=f'No Instrument found matching inst_id.')
        else:
            logger.debug('The inst_id field is missing and is required to write a Measurement.')
            raise errors.ResourceError(msg=f'The inst_id field is missing and is required to write a Measurement.')
        return utils.ok(result=[], msg=message)


# Measurements resource
class MeasurementsResource(Resource):
    """
    Work with Measurements objects
    """
    # Get measurements
    def get(self, project_id, site_id, instrument_id):
            result =[]
            msg=""
            logger.debug(f"In get measurements")
            site,msg = meta.get_site(project_id,site_id)
            logger.debug(site)
            replace_cols = {}
            for inst in site['instruments']:
                logger.debug(inst)
                if inst['inst_id'] == instrument_id:
                    instrument = inst
                    logger.debug(inst)
                    for v in inst['variables']:
                        logger.debug(v)
                        replace_cols[str(v['chords_id'])]=v['var_id']
            js= influx.query_measurments([{"inst":str(instrument['chords_id'])},{"start_date": request.args.get('start_date')},{"end_date": request.args.get('end_date')}])
            logger.debug(js)
            if len(js) > 1 and len(js['series']) > 0:
                df = pd.DataFrame(js['series'][0]['values'],columns=js['series'][0]['columns'])
                pv = df.pivot(index='time', columns='var', values=['value'])
                df1 = pv
                df1.columns = df1.columns.droplevel(0)
                df1 = df1.reset_index().rename_axis(None, axis=1)
                df1.rename(columns=replace_cols,inplace=True)
                df1.set_index('time',inplace=True)
                if request.args.get('format') == "csv":
                    logger.debug("CSV")
                    logger.debug(f"CSV in Bytess: "+ str(sys.getsizeof(df1.to_csv)))
                    output = make_response(df1.to_csv())
                    output.headers["Content-Disposition"] = "attachment; filename=export.csv"
                    output.headers["Content-type"] = "text/csv"
                    metric = {'created_at':datetime.now().isoformat(),'type':'download','project_id':project_id,'username':g.username,'size': sys.getsizeof(df1.to_csv)}
                    metric_result, metric_bug =auth.t.meta.createDocument(db=conf.tenant[g.tenant_id]['stream_db'], collection='streams_metrics', request_body=metric, _tapis_debug=True)
                    logger.debug(f' Metric result: ' +str(metric_result))
                    return output
                else:
                    result = json.loads(df1.to_json())
                    result['measurements_in_file'] = len(df1.index)
                    result['instrument'] = instrument
                    site.pop('instruments',None)
                    result['site'] = meta.strip_meta(site)
                    logger.debug("JSON in Bytes: "+ str(sys.getsizeof(result)))
                    metric = {'created_at':datetime.now().isoformat(),'type':'download','project_id':project_id,'username':g.username,'size': str(sys.getsizeof(result))}
                    metric_result, metric_bug =auth.t.meta.createDocument(db=conf.tenant[g.tenant_id]['stream_db'], collection='streams_metrics', request_body=metric, _tapis_debug=True)
                    logger.debug(metric_result)
                    return utils.ok(result=result, msg="Measurements Found")
            else:
                return utils.ok(result=[], msg="No Measurements Founds")


class MeasurementsReadResource(Resource):
    """
    Work with Measurements objects
    """
    # GET measurements
    def get(self, instrument_id):
        result =[]
        msg=""
        logger.debug("top of GET /measurements")
        #inst_result = meta.get_instrument(project_id,site_id,instrument_id)
        inst_index = meta.fetch_instrument_index(instrument_id)
        logger.debug(inst_index)
        if len(inst_index) > 0:
            logger.debug(f'Instrument index length is gt 0')
            logger.debug(inst_index['project_id'])
            site,msg = meta.get_site(inst_index['project_id'],inst_index['site_id'])
            project_id = inst_index['project_id']
            logger.debug(project_id)
            authorized = sk.check_if_authorized_post(project_id)
            logger.debug(f' Authorized: ' +str(authorized))
            if (authorized):
                logger.debug(f'User is authorized to download measurements')
                js= influx.query_measurments([{"inst":str(inst_index['chords_inst_id'])},{"start_date": request.args.get('start_date')},{"end_date": request.args.get('end_date')}])
                logger.debug(js)
                if len(js) > 1 and len(js['series']) > 0:
                    df = pd.DataFrame(js['series'][0]['values'],columns=js['series'][0]['columns'])
                    pv = df.pivot(index='time', columns='var', values=['value'])
                    df1 = pv
                    df1.columns = df1.columns.droplevel(0)
                    df1 = df1.reset_index().rename_axis(None, axis=1)
                    replace_cols = {}
                    logger.debug(site)
                    for inst in site['instruments']:
                        logger.debug(inst)
                        if inst['inst_id'] == instrument_id:
                            instrument = inst
                            logger.debug(inst)
                            for v in inst['variables']:
                                logger.debug(v)
                                replace_cols[str(v['chords_id'])]=v['var_id']
                    logger.debug(replace_cols)
                    df1.rename(columns=replace_cols,inplace=True)
                    df1.set_index('time',inplace=True)
                    if request.args.get('format') == "csv":
                        logger.debug("CSV")
                        output = make_response(df1.to_csv())
                        output.headers["Content-Disposition"] = "attachment; filename=export.csv"
                        output.headers["Content-type"] = "text/csv"
                        metric = {'created_at':datetime.now().isoformat(),'type':'download','project_id':inst_idex['project_id'],'username':g.username,'size': sys.getsizeof(df1.to_csv)}
                        metric_result, metric_bug =auth.t.meta.createDocument(db=conf.tenant[g.tenant_id]['stream_db'], collection='streams_metrics', request_body=metric, _tapis_debug=True)
                        logger.debug(metric_result)
                        return output
                    else:
                        result = json.loads(df1.to_json())
                        result['measurements_in_file'] = len(df1.index)
                        result['instrument'] = instrument
                        site.pop('instruments',None)
                        result['site'] = meta.strip_meta(site)
                        metric = {'created_at':datetime.now().isoformat(),'type':'download','project_id':inst_index['project_id'],'username':g.username,'size': str(sys.getsizeof(result))}
                        metric_result, metric_bug =auth.t.meta.createDocument(db=conf.tenant[g.tenant_id]['stream_db'], collection='streams_metrics', request_body=metric, _tapis_debug=True)
                        logger.debug(metric_result)
                        return utils.ok(result=result, msg="Measurements Found")
                else:
                    return utils.ok(result=[], msg="No Measurements Founds")
            else:
                logger.debug('User does not have any role on project')
                raise common_errors.PermissionsError(msg=f'User not authorized to access the resource')

# Measurements Resource: GET , PUT , DELETE
class MeasurementResource(Resource):
    """
    Work with Measurements objects
    """

    def get(self, instrument_id):
        logger.debug("top of GET /measurements/{measurement_id}")

    def put(self, measurement_id):
        logger.debug("top of PUT /measurements/{measurement_id}")

    def delete(self, measurement_id):
        logger.debug("top of DELETE /measurements/{measurement_id}")

# Channels resource
class ChannelsResource(Resource):
    """
    Work with channel objects
    """
    # List channels: GET /v3/streams/channels
    def get(self):
        logger.debug("top of GET /channels")
        channel_result, msg = kapacitor.list_channels()
        logger.debug(channel_result)
        result = meta.strip_meta_list(channel_result)
        logger.debug(f' Channels Result: ' +str(result))
        return utils.ok(result=result, msg=msg)

    # Create channel POST /v3/streams/channels
    def post(self):
        logger.debug("top of POST /channels")
        body = request.json
        try:
            result, msg = kapacitor.create_channel(body)
            logger.debug(f'Kapacitor create channel result: ' +str(result))
            # Channel creator will get assigned a channel admin role in SK. Any access request to the channel will check for assocaited role in SK
            channels_admin_role = 'streams_channel_' + result['_id']['$oid'] + '_admin'
            logger.debug(f' Channel admin role: '+ str(channels_admin_role))
            # Create role in SK. If role creation is successful then grant it.
            create_role_status = sk.create_role(channels_admin_role, 'Channel Admin Role')
            if (create_role_status == 'success'):
                grant_role_status = sk.grant_role(channels_admin_role, g.username)
                if (grant_role_status == 'success'):
            # Only if the role is granted, call metadata to create project collection
                    result = meta.strip_meta(result)
                    return utils.ok(result, msg=msg)
                else:
                  try:
                      delete_role_sk = sk.deleteRoleByName(roleName=channels_admin_role, tenant=g.tenant_id)
                      logger.debug(f'channels admin role deleted from SK')
                      msg = f"Could not create channel"
                      return utils.error(result='null', msg=msg)
                  except Exception as e:
                    msg = f"Cound not delete role: {channels_admin_role};"
                    return utils.error(result='null', msg=msg)

            else:
                msg = f"Could not create channel"
                return utils.error(result='null', msg=msg)
        except Exception as e:
            msg = f"Could not create channel: " + e.msg
            return utils.error(result='null', msg=msg)
        return utils.error(result='null', msg=msg)

# Channel resource: GET, PUT, POST, DELETE
class ChannelResource(Resource):
    """
    Work with Streams objects
    """
    # Get channel details GET /v3/streams/channels/<channel_id>
    def get(self, channel_id):
        logger.debug("top of GET /channels/{channel_id}")
        # Check if the user is authorized to access the channel by checking the user has project specific role in sk
        authorized = sk.check_if_authorized_get_channel(channel_id)
        if (authorized):
            logger.debug(f'User is authorized to access project : ' + str(channel_id))
            channel_result, msg = kapacitor.get_channel(channel_id)
            logger.debug(f'Kapacitor get channel result: '+str(channel_result))
            result = meta.strip_meta(channel_result)
            logger.debug(result)
            return utils.ok(result=result, msg=msg)
        else:
            logger.debug(f'User does not have any role on the channel: ' + str(channel_id))
            raise common_errors.PermissionsError(msg=f'User not authorized to access the resource')

    # Update Channel PUT /v3/streams/channels/<channel_id>
    def put(self, channel_id):
        logger.debug("top of PUT /channels/{channel_id}")
        body = request.json
        result = {}
        logger.debug(f'Check if the user is authorized to update the channel ')
        authorized = sk.check_if_authorized_put_channel(channel_id)
        if (authorized):
            try:
                result, msg = kapacitor.update_channel(channel_id, body)
            except Exception as e:
                msg = f"Could not update the channel: {channel_id}; exception: {e}"
            logger.debug(f'Update channel result: ' + str(result))
            return utils.ok(result=meta.strip_meta(result), msg=msg)
        else:
            logger.debug(f'User does not have admin or manager role on the channel: ' + str(channel_id))
            raise common_errors.PermissionsError(msg=f'User not authorized to access the resource')

    # Update channel status POST
    def post(self,channel_id):
        logger.debug("top of POST /channels/{channel_id}")
        body = request.json
        logger.debug(f'Check if the user is authorized to update the channel status')
        authorized = sk.check_if_authorized_post_channel(channel_id)
        if (authorized):
            # TODO Convert to Status Enum
            if body['status']== 'ACTIVE':
                body['status']='enabled'
            elif body['status']== 'INACTIVE':
                body['status'] = 'disabled'
                logger.debug(body)
            else:
                raise errors.ResourceError(msg=f'Invalid POST data: {body}.')
            result = {}
            try:
                result, msg = kapacitor.update_channel_status(channel_id,body)
            except Exception as e:
                logger.debug(type(e))
                logger.debug(e.args)
                msg = f"Could not update the channel status: {channel_id}; exception: {e} "
                logger.debug(msg)
            logger.debug(result)
            if result:
                return utils.ok(result=meta.strip_meta(result), msg=msg)
            return utils.error(result=result, msg=msg)
        else:
            logger.debug(f'User does not have admin or manager role on the channel: ' + str(channel_id))
            raise common_errors.PermissionsError(msg=f'User not authorized to access the resource')

    def delete(self, channel_id):
        logger.debug("top of DELETE /channels/{channel_id}")

class AlertsResource(Resource):
    """"
    Alerts Resource
    """
    def get(self,channel_id):
        logger.debug("top of GET /channels/{channel_id}/alerts")
        logger.debug(channel_id)
        result, msg = meta.list_alerts(channel_id)
        logger.debug(result)
        result_meta = meta.strip_meta_list(result)
        num_of_alerts = len(result_meta)
        result_alerts = {}
        result_alerts['num_of_alerts'] = num_of_alerts
        result_alerts['alerts'] = result_meta
        return utils.ok(result=result_alerts,msg=msg)

class AlertsPostResource(Resource):
    def get(self):
        logger.debug("top of GET /alerts")
        result = ''
        msg = ''
        return utils.ok(result=result,msg=msg)
    def post(self):
        logger.debug("top of POST /alerts")

        try:
            req_data = json.loads(request.get_data())
            logger.debug(req_data)
        except:
            logger.debug('Invalid POST JSON data')
            raise errors.ResourceError(msg=f'Invalid POST data: {req_data}.')

        #parse 'id' field, first string is the channel_id
        channel_id = req_data['id'].split(" ")[0]

        # prepare request for Abaco
        channel, msg = kapacitor.get_channel(channel_id)
        logger.debug(channel)
        result, message = abaco.create_alert(channel,req_data)
        logger.debug("end of POST /alerts")

        return utils.ok(result=result, msg=message)

class TemplatesResource(Resource):
    """
    Work with Streams-Channels-Templates objects
    """
    # GET templates
    # permission check in template object permission field
    def get(self):
        logger.debug("top of GET /templates")
        template_result, msg = meta.list_templates()
        logger.debug(template_result)
        result = meta.strip_meta_list(template_result)
        logger.debug(result)
        return utils.ok(result=result, msg=msg)

    # POST template
    def post(self):
        logger.debug("top of POST /templates")
        body = request.json
        result, msg = kapacitor.create_template(body)
        logger.debug(result)
        #if template was created
        if (result['_id']['$oid']):
            #Create Admin Role for owner of template
            temp_admin_role="streams_template_"+result['_id']['$oid']+"_admin"
            create_role_status = sk.create_role(temp_admin_role, 'Project Admin Role')
            if (create_role_status == 'success'):
               grant_role_status = sk.grant_role(temp_admin_role)
               # Check if the role was granted successfully to the user
               if (grant_role_status == 'success'):
                   # Only if the role is granted to user
                   if (str(result) != 'null'):
                    return utils.ok(result=meta.strip_meta(result), msg=msg)
               # If role granting was not success, we should cleanup the role from sk
               else:
                   try:
                     delete_role_sk = sk.deleteRoleByName(roleName=temp_admin_role,tenant=g.tenant_id)
                     logger.debug(f'Template admin role deleted from SK: '+str(temp_admin_role))
                     msg = f"Could not create Template"
                     return utils.error(result='null', msg=msg)
                   except Exception as e:
                       msg = f"Cound not delete role: {temp_admin_role};"
                       return utils.error(result='null', msg=msg)
            else:
                msg = f"Could not create Template"
                return utils.error(result='null', msg=msg)
        else:
            msg = f"Could not create Template"
            return utils.error(result='null', msg=msg)


class TemplateResource(Resource):
    """
    Work with Streams objects
    """
    # GET template
    # permission check in template object permission field
    def get(self, template_id):
        logger.debug("top of GET /templates/{template_id}")
        template_result, msg = kapacitor.get_template(template_id)
        logger.debug(str(template_result))
        result = meta.strip_meta(template_result)
        logger.debug(result)
        return utils.ok(result=result, msg=msg)

    def post(self, template_id):
        logger.debug("top of POST /templates/{template_id}")

    # PUT template
    # permission checked in sk role
    def put(self,template_id):
        logger.debug("top of PUT /templates/{template_id}")
        body = request.json
        result = {}
        authorized = sk.check_if_authorized_put_template(template_id)
        if (authorized):
            logger.debug(f'User is authorized to update template : '+str(template_id))
            try:
                result, msg = kapacitor.update_template(template_id,body)
                logger.debug(str(result))
                return utils.ok(result=meta.strip_meta(result), msg=msg)
            except Exception as e:
                msg = f"Could not update the template status: {template_id}; exception: {e}"
                raise common_errors.ResourceError(msg=msg)
        else:
            logger.debug(f'User does not have Admin or Manager role on the template: '+ str(template_id))
            raise common_errors.PermissionsError(msg=f'User not authorized to access the resource')


    # Delete Template ToDo
    # permission check sk role
    def delete(self, template_id):
        logger.debug("top of DELETE /channels/{channel_id}")

# Influx Resource
class InfluxResource(Resource):
    #Expect fields[] parameters
    #EXAMPLE: fields[]={"inst":1}&fields[]={"var":1}
    # GET /influx
    def get(self):
        logger.debug(f'Inside GET /influx')
        logger.debug(request.args)
        field_list = request.args.getlist('fields[]')
        #expects instrument_id=1&vars[]={"somename":1.0}&vars[]={"other":2.0} in the request.args
        resp = influx.query_measurments(field_list)
        logger.debug(resp)
        return resp


    def post(self):
        logger.debug(f'Inside POST /influx')
        logger.debug(request.args)
        #expects instrument_id=1&vars[]={"somename":1.0}&vars[]={"other":2.0} in the request.args
        resp = influx.create_measurement(request.args.get('site_id'), request.args.get('inst_id'), request.args.get('var_id'),  float(request.args.get('value')), request.args.get('timestamp'), )
        logger.debug(resp)
        return resp

# Metrics Resource for reporting
class MetricsResource(Resource):
    # GET /v3/streams/metrics
    def get(self):
      #todo parse a start and end date for a query
      result = auth.t.meta.listDocuments(db=conf.tenant[g.tenant_id]['stream_db'],collection='streams_metrics')
      logger.debug(json.loads(result.decode('utf-8')))
      return json.loads(result.decode('utf-8'))

# Role management for different resource
class PemsResource(Resource):
    def get(self):
        # Expect user=testuser&resource_type={project/channels}&resource_id={project_id/channel_id}
        logger.debug(f'Inside GET /roles')
        logger.debug(request.args)
        user = request.args.get('user')
        resource_type = request.args.get('resource_type')
        resource_id = request.args.get('resource_id')
        # This method will return roles for user specified in the query parameters
        # jwt_user_flag is set to False as we need roles for user in the query parameters and not the initiating the request
        roles,msg = sk.check_user_has_role(user, resource_type,resource_id, False)
        logger.debug(roles)
        # if roles is not empty, that means the user has some or all role on the resource id, which are returned in result
        if roles:
            return utils.ok(result=roles, msg=msg)
        # if roles is empty that means no roles are found for user specified in the query parameters
        else:
            return utils.ok(result='', msg=msg)

    def post(self):
        logger.debug(f'Inside POST /roles')
        logger.debug(f'Request body: ' + str(request.json))
        body = request.json
        req_body = body
        legal_roles = ['admin', 'manager', 'user']
        username = req_body['user']
        resource_type = req_body['resource_type']
        resource_id = req_body['resource_id']
        role_name = req_body['role_name']
        # the role_name is not admin, manager or user return error message
        if (role_name not in legal_roles):
            msg = f'Invalid role name'
            logger.debug(msg)
            return utils.error(result='', msg=msg)
        # if the jwt user and user in request body is same, self permission assigning is not allowed
        if (username == g.username):
            roles, msg = sk.check_user_has_role(username, resource_type, resource_id,True)
            # check if the role the user is requesting already exists
            if role_name in roles:
                msg = f'Role already exists'
                logger.debug(msg)
                return utils.ok(result=roles, msg=msg)
            else:
                msg = f'Cannot grant role for self'
                logger.debug(msg)
                return utils.error(result='', msg=msg)
        # If the jwt user and user in req body are different
        else:
            # get the user roles for user in the request body
            user_roles, msg = sk.check_user_has_role(username, resource_type, resource_id, False)
            # Check if the role already exists
            if role_name in user_roles:
                msg = f'Role already exists'
                logger.debug(msg)
                return utils.ok(result=user_roles, msg=msg)
            else:
                # jwt user can only grant similar or lower roles to requesting users
                # For example if jwt user is admin: admin, manager or user roles can be granted to requesting user
                jwt_user_roles, msg = sk.check_user_has_role(g.username, resource_type, resource_id, True)
                logger.debug(jwt_user_roles)
                if 'admin' in (jwt_user_roles):
                     new_role, msg = sk.grant_role_user_asking(resource_id,role_name, resource_type,username)
                     user_roles.append(new_role)
                     return utils.ok(result=user_roles, msg=msg)
                # If the jwt user is manager, they cannot grant admin roles to other users
                # 'Manager' and 'User' roles can be granted to other users
                elif 'manager' in (jwt_user_roles):
                    if role_name == 'admin':
                        msg = f'Role ' + role_name + f' cannot be granted'
                        logger.debug(msg)
                        return utils.error(result='', msg=msg)
                    else:
                        # Grant role the user in request body is asking for
                        new_role, msg = sk.grant_role_user_asking(resource_id, role_name, resource_type, username)
                        user_roles.append(new_role)
                        # return the updated roles list to user
                        return utils.ok(result=user_roles, msg=msg)
                # if the jwt user is only has a user role, no roles can be granted by them
                elif 'user' in (jwt_user_roles):
                    msg = f'Role ' + role_name + f' cannot be granted'
                    logger.debug(msg)
                    return utils.error(result='', msg=msg)
                else:
                    msg = f'User not authorized to grant role'
                    logger.debug(msg)
                    return utils.error(result='', msg=msg)

class PemsRevokeResource(Resource):
    def post(self):
        logger.debug(f'Inside  /roles/revokeRole')
        logger.debug(f'Request body: ' + str(request.json))
        body = request.json
        req_body = body
        legal_roles = ['admin', 'manager', 'user']
        username = req_body['user']
        resource_type = req_body['resource_type']
        resource_id = req_body['resource_id']
        role_name = req_body['role_name']
        # the role_name is not admin, manager or user return error message
        if (role_name not in legal_roles):
            msg = f'Invalid role name'
            logger.debug(msg)
            return utils.error(result='', msg=msg)
        # if the jwt user and user in request body is same, self permission assigning is not allowed
        if (username == g.username):
            msg = f'Cannot delete role for self'
            logger.debug(msg)
            return utils.error(result='', msg=msg)
        # If the jwt user and user in req body are different
        else:
            # If jwt_user is admin, then only delete role
            # getting the jwt user role
            jwt_user_roles, msg = sk.check_user_has_role(g.username, resource_type, resource_id, True)
            logger.debug(jwt_user_roles)
            if 'admin' in (jwt_user_roles):
                # get the user roles for user in the request body
                user_roles, msg = sk.check_user_has_role(username, resource_type, resource_id, False)
                logger.debug(user_roles)
                if role_name not in user_roles:
                    msg = f'Role does not exists'
                    logger.debug(msg)
                    return utils.error(result='', msg=msg)
                delete_role, msg = sk.delete_role_user_asking(resource_id,role_name, resource_type,username)
                return utils.ok(result='', msg=msg)
                # If the jwt user is manager, no roles can be deleted
            elif 'manager' in (jwt_user_roles):
                msg = f'User not authorized to revoke role'
                logger.debug(msg)
                return utils.error(result='', msg=msg)

            # if the jwt user is only has a user role, no roles can be deleted
            elif 'user' in (jwt_user_roles):
                msg = f'User not authorized to revoke role'
                logger.debug(msg)
                return utils.error(result='', msg=msg)
            else:
                msg = f'User not authorized to revoke role'
                logger.debug(msg)
                return utils.error(result='', msg=msg)
