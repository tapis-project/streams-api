import datetime
from flask import request, make_response
from flask_restful import Resource
from openapi_core.shortcuts import RequestValidator
from openapi_core.wrappers.flask import FlaskOpenAPIRequest
# import psycopg2
#import sqlalchemy
import chords
import influx
import meta
import kapacitor
import abaco
import sk
from models import ChordsSite, ChordsIntrument, ChordsVariable
from common import utils, errors
from common.config import conf
from requests.auth import HTTPBasicAuth
from common import errors as common_errors

#from service.models import db, LDAPConnection, TenantOwner, Tenant

import requests
import json
import pandas as pd
# get the logger instance -
from common.logs import get_logger
logger = get_logger(__name__)

class HelloResource(Resource):
    def get(self):
        logger.debug('In hello resource')
        return utils.ok(result='',msg="Hello from Streams")

class ReadyResource(Resource):
    def get(self):
        try:
            logger.debug('Kapacitor status')
            status_kapacitor=kapacitor.ping()
            logger.debug(status_kapacitor)
            status_chords=chords.ping()
            logger.debug('Chords status')
            logger.debug(status_chords)
            status_influx = influx.ping()
            logger.debug('Influx status')
            logger.debug(status_influx)
            if(status_kapacitor == 204 and status_chords == 200 and status_influx == 204):
                return utils.ok(result='', msg=f'Service ready')
        except:
            raise errors.ResourceError(msg=f'Service not ready')

class HealthcheckResource(Resource):
    def get(self):
        try:
            status_kapacitor = kapacitor.ping()
            logger.debug('Kapacitor status')
            logger.debug(status_kapacitor)
        except:
            raise errors.ResourceError(msg=f'Kapacitor not ready')
        try:
            status_chords = chords.ping()
            logger.debug('Chords status')
            logger.debug(status_chords)
        except:
            raise errors.ResourceError(msg=f'Chords not ready')
        try:
            status_influx = influx.ping()
            logger.debug('Influx status')
            logger.debug(status_influx)
        except:
            raise errors.ResourceError(msg=f'Influx DB not ready')
        try:
            logger.debug('Meta status')
            status_meta = meta.healthcheck()
            logger.debug(status_meta)
        except:
            raise errors.ResourceError(msg=f'Metadata not ready')
        return utils.ok(result='',msg="Streams in good health")

class ProjectsResource(Resource):
    """
    Work with Project objects
    """
    def get(self):
            logger.debug('In list projects')
            proj_result, msg = meta.list_projects()
            result = meta.strip_meta_list(proj_result)
            logger.debug('After list projects')
            return utils.ok(result=result,msg=msg)


    def post(self):
        logger.debug(request.json)
        body = request.json
        req_body = body
        # Project creator will be assigned admin role.

        try:
            proj_result, msg = meta.create_project(body)
            logger.debug(proj_result)
            proj_admin_role = 'streams_' + proj_result['_id']['$oid'] + '_admin'
            logger.debug(proj_admin_role)
            # Create role in SK. If role creation is successful then grant it.
            create_role_status = sk.create_role(proj_admin_role, 'Project Admin Role')
            if (create_role_status == 'success'):
               grant_role_status = sk.grant_role(proj_admin_role)
               if (grant_role_status == 'success'):
                   # Only if the role is granted, call metadata to create project collection

                   if (str(proj_result) != 'null'):
                    result = meta.strip_meta(proj_result)
                    return utils.ok(result, msg=msg)
               else:
                   try:
                     # If role granting was not success, we should cleanup the role from sk
                     delete_role_sk = sk.deleteRoleByName(roleName=proj_admin_role,tenant=g.tenant_id)
                     logger.debug('proj admin role deleted from SK')
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
        #msg = 'Project creation failed'
        return utils.error(result='null', msg=msg)
        #resp['status'] = result['status']
        #logger.debug(meta_resp['status'])
        #logger.debug(resp)


class ProjectResource(Resource):
    """
    Work with Project objects
    """

    def get(self, project_id):
        authorized = sk.check_if_authorized_get(project_id)
        if(authorized) is True:
            logger.debug("Authorized user")
            proj_result, msg = meta.get_project(project_id)
            result = meta.strip_meta(proj_result)
            logger.debug(result)
            return utils.ok(result=result, msg=msg)
        else:
            logger.debug('User does not have any role on the project')
            raise common_errors.PermissionsError(msg=f'User not authorized to access the resource')

    def put(self, project_id):
        authorized = sk.check_if_authorized_put(project_id)
        if (authorized):
            body = request.json
            proj_result, msg = meta.update_project(project_id, body)
            result = meta.strip_meta(proj_result)
            return utils.ok(result=result, msg=msg)
        else:
            logger.debug('User does not have Admin or Manager role on the project')
            raise common_errors.PermissionsError(msg=f'User not authorized to access the resource')

    def delete(self, project_id):
        #return ""
        #proj_result, msg = meta.get_project(project_id)
        authorized = sk.check_if_authorized_delete(project_id)
        if (authorized):
             proj_result, msg = meta.delete_project(project_id)
             result = meta.strip_meta(proj_result)
             return utils.ok(result=result, msg=msg)
        else:
            logger.debug('User does not have Admin role on the project')
            raise common_errors.PermissionsError(msg=f'User not authorized to access the resource')


class SitesResource(Resource):
    """
    Work with Sites objects
    """

    #TODO metadata integration - need to use query, limit and offset
    def get(self, project_id):
        authorized = sk.check_if_authorized_get(project_id)
        logger.debug(authorized)
        if (authorized):
            site_result, msg = meta.list_sites(project_id)
            result = meta.strip_meta_list(site_result)
            return utils.ok(result=result,msg=msg)
        else:
            logger.debug('authorization failed')
            logger.debug('User does not have role on the project')
            raise common_errors.PermissionsError(msg=f'User not authorized to access the resource')

    def post(self, project_id):
        # validator = RequestValidator(utils.spec)
        # result = validator.validate(FlaskOpenAPIRequest(request))
        # if result.errors:
        #     raise errors.ResourceError(msg=f'Invalid POST data: {result.errors}.')
        # validated_params = result.parameters
        # validated_body = result.body
        # logger.debug(f"validated_body: {dir(validated_body)}")

        #need to add check for project permission & project exists before chords insertion
        authorized = sk.check_if_authorized_post(project_id)
        logger.debug(authorized)
        if (authorized):
                logger.debug("Inside if")
                logger.debug(request.json)
                body = request.json
                postSite = ChordsSite("",body['site_name'],
                                        body['latitude'],
                                        body['longitude'],
                                        body['elevation'],
                                        body['description'])
                resp, msg = chords.create_site(postSite)
                if msg == "Site created":
                    site_result, message = meta.create_site(project_id, resp['id'],body)
                    #resp['results']=meta_resp['results']
                    logger.debug('success')
                    logger.debug(site_result)
                    result = meta.strip_meta(site_result)
                    #meta_resp, getmsg = meta.get_site(project_id, resp['id'])
                else:
                    logger.debug('failed')
                    message = msg
                    result=''
                return utils.ok(result=result,msg=message)
        else:
            logger.debug('User does not have Admin or Manager role on the project')
            raise common_errors.PermissionsError(msg=f'User not authorized to access the resource')


class SiteResource(Resource):
    """
    Work with Sites objects
    """
    def get(self, project_id, site_id):
        authorized = sk.check_if_authorized_get(project_id)
        if(authorized):
            site_result, msg = meta.get_site(project_id,site_id)
            result = meta.strip_meta(site_result)
            logger.debug(result)
            return utils.ok(result=result, msg=msg)
        else:
            logger.debug('User does not have any role on project')
            raise common_errors.PermissionsError(msg=f'User not authorized to access the resource')

    def put(self, project_id, site_id):
        authorized = sk.check_if_authorized_put(project_id)
        if (authorized):
            body = request.json
            site_result, msg = meta.update_site(project_id, site_id, body)
            result = meta.strip_meta(site_result)
            putSite = ChordsSite(result['chords_id'],
                                  body['site_name'],
                                  body['latitude'],
                                  body['longitude'],
                                  body['elevation'],
                                  body['description'])
            chord_result, chord_msg = chords.update_site(result['chords_id'], putSite)
            return utils.ok(result=result, msg=msg)
        else:
            logger.debug('User does not have Admin or Manager role on the project')
            raise common_errors.PermissionsError(msg=f'User not authorized to access the resource')

    def delete(self, project_id, site_id):
        authorized = sk.check_if_authorized_delete(project_id)
        if (authorized):
            #result, msg = chords.delete_site(site_id)
            site_result, msg = meta.delete_site(project_id,site_id)
            logger.debug(msg)
            return utils.ok(result=site_result, msg=f'Site {site_id} deleted.')
        else:
            logger.debug('User does not have Admin role on the project')
            raise common_errors.PermissionsError(msg=f'User not authorized to access the resource')


class InstrumentsResource(Resource):
    """
    Work with Instruments objects
    """
    def get(self,project_id,site_id):
        authorized = sk.check_if_authorized_get(project_id)
        if (authorized):
        #result,msg = chords.list_instruments()
            result,msg = meta.list_instruments(project_id, site_id)
            logger.debug(site_id)
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
            logger.debug('User does not have any role on project')
            raise common_errors.PermissionsError(msg=f'User not authorized to access the resource')


    #TODO support bulk create operations
    def post(self, project_id, site_id):
        authorized = sk.check_if_authorized_post(project_id)
        if (authorized):
            logger.debug(type(request.json))
            logger.debug(request.json)
            result={}
            #TODO loop through list objects to support build operations
            if type(request.json) is dict:
                body = request.json
            else:
                body = request.json[0]
            logger.debug('before ChordsInstrument assignment')
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
                logger.debug('after ChordsInstrument assignment')
                chord_result, chord_msg = chords.create_instrument(postInst)
                if chord_msg == "Instrument created":
                    body['chords_id'] = chord_result['id']
                    #body['instrument_id'] = instrument_id
                    inst_result, inst_msg = meta.create_instrument(project_id, site_id, body)
                    logger.debug(inst_msg)
                    if len(inst_result) >0:
                        result = inst_result
                        message = inst_msg
                else:
                    message = chord_msg
            else:
                message = "Site Failed To Create"
            return utils.ok(result=result, msg=message)
        else:
            logger.debug('User does not have Admin or Manager role on project')
            raise common_errors.PermissionsError(msg=f'User not authorized to access the resource')


class InstrumentResource(Resource):
    """
    Work with Instruments objects
    """
    def get(self, project_id, site_id, instrument_id):
        authorized = sk.check_if_authorized_get(project_id)
        if (authorized):
            #result,msg = chords.get_instrument(instrument_id)
            result,msg = meta.get_instrument(project_id, site_id,instrument_id)
            return utils.ok(result=result, msg=msg)
        else:
            logger.debug('User does not have any role on project')
            raise common_errors.PermissionsError(msg=f'User not authorized to access the resource')

    def put(self, project_id, site_id, instrument_id):
        authorized = sk.check_if_authorized_put(project_id)
        if (authorized):
            logger.debug(type(request.json))
            logger.debug(request.json)
            #TODO loop through list objects to support buld operations
            if type(request.json) is dict:
                body = request.json
            else:
                body = request.json[0]

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
            chord_result, chord_msg = chords.update_instrument(str(result['chords_id']), putInst)
            return utils.ok(result=result, msg=msg)
        else:
            logger.debug('User does not have Admin or Manager role on the project')
            raise common_errors.PermissionsError(msg=f'User not authorized to access the resource')


    def delete(self, project_id, site_id, instrument_id):
        authorized = sk.check_if_authorized_delete(project_id)
        if (authorized):
            #chord_result,chord_msg = chords.delete_instrument(instrument_id)
            result, msg = meta.update_instrument(project_id, site_id, instrument_id, {},True)
            return utils.ok(result={}, msg=msg)
        else:
            logger.debug('User does not have admin role on the project')
            raise common_errors.PermissionsError(msg=f'User not authorized to access the resource')


class VariablesResource(Resource):
    """
    Work with Variables objects
    """

    def get(self, project_id, site_id, instrument_id):
        authorized = sk.check_if_authorized_get(project_id)
        if (authorized):
            #result,msg = chords.list_variables()
            result, msg = meta.list_variables(project_id, site_id, instrument_id)
            logger.debug(instrument_id)
            return utils.ok(result=result, msg=msg)
        else:
            logger.debug('User does not have any role on project')
            raise common_errors.PermissionsError(msg=f'User not authorized to access the resource')


    def post(self, project_id, site_id, instrument_id):
        #logger.debug(type(request.json))
        authorized = sk.check_if_authorized_post(project_id)
        if (authorized):
            logger.debug(request.json)
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
            chord_result, chord_msg = chords.create_variable(postInst)
            if chord_msg == "Variable created":
                body['chords_id'] = chord_result['id']
                result, msg = meta.create_variable(project_id, site_id, instrument_id, body)
            else:
                message = chord_msg
            logger.debug(result)
            return utils.ok(result=result, msg=msg)
        else:
            logger.debug('User does not have admin or manager role on project')
            raise common_errors.PermissionsError(msg=f'User not authorized to access the resource')


class VariableResource(Resource):
    """
    Work with Variables objects
    """
    def get(self, project_id, site_id, instrument_id, variable_id):
        authorized = sk.check_if_authorized_get(project_id)
        if (authorized):
            #chords_result,chords_msg = chords.get_variable(variable_id)
            result, msg = meta.get_variable(project_id, site_id, instrument_id, variable_id)
            logger.debug(result)
            return utils.ok(result=result, msg=msg)
        else:
            logger.debug('User does not have any role on project')
            raise common_errors.PermissionsError(msg=f'User not authorized to access the resource')

    def put(self,project_id, site_id, instrument_id,  variable_id):
        authorized = sk.check_if_authorized_put(project_id)
        if (authorized):
            logger.debug(type(request.json))
            logger.debug(request.json)
            #TODO loop through list objects to support buld operations
            if type(request.json) is dict:
                body = request.json
            else:
                body = request.json[0]
            # id, name, instrument_id, shortname, commit
            result, msg = meta.update_variable(project_id, site_id, instrument_id, variable_id, body)
            putInst = ChordsVariable(result['chords_id'],result['inst_chords_id'],
                                        body['var_name'],
                                        body['shortname'],
                                        "")
            logger.debug(putInst)
            chord_result,chord_msg = chords.update_variable(result['chords_id'],putInst)
            logger.debug(result)
            return utils.ok(result=result, msg=msg)
        else:
            logger.debug('User does not have admin or manager role on project')
            raise common_errors.PermissionsError(msg=f'User not authorized to access the resource')


    def delete(self, project_id, site_id, instrument_id, variable_id):
        authorized = sk.check_if_authorized_delete(project_id)
        if (authorized):
            result, msg = meta.update_variable(project_id, site_id, instrument_id, variable_id, {},True)
            #chords_result, chords_msg = chords.delete_variable(result['chords_id'])
            logger.debug(result)
            return utils.ok(result=result, msg=msg)
        else:
            logger.debug('User does not have admin role on project')
            raise common_errors.PermissionsError(msg=f'User not authorized to access the resource')


class MeasurementsWriteResource(Resource):
    #at the moment expects some like
    #http://localhost:5000/v3/streams/measurements?instrument_id=1&vars[]={"somename":1.0}&vars[]={"other":2.0}
    #will need to adjust when openAPI def is final for measurement
    def post(self):
        body = request.json
        logger.debug(body)
        instrument = {}
        if 'inst_id' in body:
            logger.debug("INSIDE IF : write measurement")
            result = meta.fetch_instrument_index(body['inst_id'])
            logger.debug("After Meta : write measurement")
            logger.debug(result)
            if len(result) > 0:
                logger.debug(result[0]['chords_inst_id'])
                #get isntrument
                site_result, site_msg = meta.get_site(result[0]['project_id'],result[0]['site_id'])
                if 'instruments' in site_result:
                    for inst in site_result['instruments']:
                        if inst['inst_id'] == body['inst_id']:
                            instrument = inst
                    logger.debug(site_result)
                    project_id=result[0]['project_id']
                    logger.debug(project_id)
                    authorized = sk.check_if_authorized_post(project_id)
                    logger.debug(authorized)
                    #if (authorized):
                    #resp = chords.create_measurement(result[0]['chords_inst_id'], body)
                    if (authorized):
                        resp = influx.write_measurements(site_result['chords_id'],instrument,body)
                        logger.debug(resp)
                        return utils.ok(result=[], msg="Measurements Saved")
                    else:
                        logger.debug('User does not have admin or manager role on project')
                        raise common_errors.PermissionsError(msg=f'User not authorized to access the resource')

                    #else:
                    #    logger.debug('User does not have admin role on project')
                    #    raise common_errors.PermissionsError(msg=f'User not authorized to access the resource')


class MeasurementsResource(Resource):
    """
    Work with Measurements objects
    """
    def get(self, project_id, site_id, instrument_id):
            result =[]
            msg=""
            logger.debug("top of GET /measurements")
            #inst_result = meta.get_instrument(project_id,site_id,instrument_id)
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
                    # csv_response = Response(result, mimetype="text/csv")
                    # si = StringIO.StringIO()
                    #cw = csv.write(si)
                    # cw.writerows(csvList)
                    output = make_response(df1.to_csv())
                    output.headers["Content-Disposition"] = "attachment; filename=export.csv"
                    output.headers["Content-type"] = "text/csv"
                    return output
                else:
                    result = json.loads(df1.to_json())
                    result['measurements_in_file'] = len(df1.index)
                    result['instrument'] = instrument
                    site.pop('instruments',None)
                    result['site'] = meta.strip_meta(site)
                    return utils.ok(result=result, msg="Measurements Found")
            else:
                return utils.ok(result=[], msg="No Measurements Founds")
            # logger.debug("top of GET /measurements")
            # #inst_result = meta.get_instrument(project_id,site_id,instrument_id)
            # inst_index = meta.fetch_instrument_index(instrument_id)
            # logger.debug(inst_index)
            # if len(inst_index) > 0:
            #     result,msg = chords.get_measurements(str(inst_index[0]['chords_inst_id']),request.args.get('start_date'),request.args.get('end_date'),request.args.get('format'))
            #     logger.debug(result)
            # #return utils.ok(result=list(map(lambda t: list(map(lambda r: {'units':r.units,'value':r.value,'variable_name':r.variable_name,'varable_id':r.shortname}, t['vars'])),result['features'][0 ]['properties']['data'])), msg=msg)
            # if request.args.get('format') == "csv":
            #     logger.debug("CSV")
            #     # csv_response = Response(result, mimetype="text/csv")
            #     # si = StringIO.StringIO()
            #     #cw = csv.write(si)
            #     # cw.writerows(csvList)
            #     output = make_response(result)
            #     output.headers["Content-Disposition"] = "attachment; filename=export.csv"
            #     output.headers["Content-type"] = "text/csv"
            #     return output
            # else:
            #     logger.debug("JSON")
            #     return utils.ok(result={"data":result['features'][0 ]['properties']['data'],"measurements_in_file": result['features'][0 ]['properties']['measurements_in_file']}, msg=msg)


class MeasurementsReadResource(Resource):
    """
    Work with Measurements objects
    """
    def get(self, instrument_id):
        result =[]
        msg=""
        logger.debug("top of GET /measurements")
        #inst_result = meta.get_instrument(project_id,site_id,instrument_id)
        inst_index = meta.fetch_instrument_index(instrument_id)
        logger.debug(inst_index)
        if len(inst_index[0]) > 0:
            site,msg = meta.get_site(inst_index[0]['project_id'],inst_index[0]['site_id'])
            project_id = inst_index[0]['project_id']
            logger.debug(project_id)
            authorized = sk.check_if_authorized_post(project_id)
            logger.debug(authorized)
            if (authorized):
                js= influx.query_measurments([{"inst":str(inst_index[0]['chords_inst_id'])},{"start_date": request.args.get('start_date')},{"end_date": request.args.get('end_date')}])
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
                        # csv_response = Response(result, mimetype="text/csv")
                        # si = StringIO.StringIO()
                        #cw = csv.write(si)
                        # cw.writerows(csvList)
                        output = make_response(df1.to_csv())
                        output.headers["Content-Disposition"] = "attachment; filename=export.csv"
                        output.headers["Content-type"] = "text/csv"
                        return output
                    else:
                        result = json.loads(df1.to_json())
                        result['measurements_in_file'] = len(df1.index)
                        result['instrument'] = instrument
                        site.pop('instruments',None)
                        result['site'] = meta.strip_meta(site)
                        return utils.ok(result=result, msg="Measurements Found")
                else:
                    return utils.ok(result=[], msg="No Measurements Founds")
            else:
                logger.debug('User does not have any role on project')
                raise common_errors.PermissionsError(msg=f'User not authorized to access the resource')


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

class ChannelsResource(Resource):
    """
    Work with Streams objects
    """

    def get(self):
        logger.debug("top of GET /channels")
        channel_result, msg = kapacitor.list_channels()
        logger.debug(channel_result)
        result = meta.strip_meta_list(channel_result)
        logger.debug(result)
        return utils.ok(result=result, msg=msg)

    def post(self):
        logger.debug("top of POST /channels")
        body = request.json
        #TODO need to check user permissions
        result, msg = kapacitor.create_channel(body)
        logger.debug(result)
        logger.debug("end of POST /channels.. returning result to user")
        return utils.ok(result=meta.strip_meta(result), msg=msg)



class ChannelResource(Resource):
    """
    Work with Streams objects
    """

    def get(self, channel_id):
        logger.debug("top of GET /channels/{channel_id}")
        channel_result, msg = kapacitor.get_channel(channel_id)
        logger.debug(channel_result)
        result = meta.strip_meta(channel_result)
        logger.debug(result)
        return utils.ok(result=result, msg=msg)

    def put(self, channel_id):
        logger.debug("top of PUT /channels/{channel_id}")

        body = request.json
        # TODO need to check the user permission to update channel status
        #if body['channel_id'] != channel_id:
        #    raise errors.ResourceError(msg=f'Invalid PUT data: {body}. You cannot change channel id')
        result = {}
        try:
            result, msg = kapacitor.update_channel(channel_id, body)
        except Exception as e:
            msg = f"Could not update the channel: {channel_id}; exception: {e}"

        logger.debug(result)
        return utils.ok(result=meta.strip_meta(result), msg=msg)

    def post(self,channel_id):
        logger.debug("top of POST /channels/{channel_id}")
        body = request.json
        # TODO need to check the user permission to update channel status
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
        logger.debug("top of GET /channels/{channel_id}/alerts")
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

    def get(self):
        logger.debug("top of GET /templates")
        template_result, msg = meta.list_templates()
        logger.debug(template_result)
        result = meta.strip_meta_list(template_result)
        logger.debug(result)
        return utils.ok(result=result, msg=msg)

    def post(self):
        logger.debug("top of POST /tempates")
        body = request.json
        #TODO need to check our permissions
        result, msg = kapacitor.create_template(body)
        logger.debug(result)
        return utils.ok(result=meta.strip_meta(result), msg=msg)

class TemplateResource(Resource):
    """
    Work with Streams objects
    """

    def get(self, template_id):
        logger.debug("top of GET /templates/{template_id}")
        template_result, msg = kapacitor.get_template(template_id)
        logger.debug(str(template_result))
        result = meta.strip_meta(template_result)
        logger.debug(result)
        return utils.ok(result=result, msg=msg)

    def post(self, template_id):
        logger.debug("top of POST /templates/{template_id}")

    def put(self,template_id):
        logger.debug("top of PUT /templates/{template_id}")
        body = request.json
        # TODO need to check the user permission to update template

        #if body['template_id'] != template_id:
        #    raise errors.ResourceError(msg=f'Invalid PUT data: {body}. You cannot change template_id')

        result = {}
        try:
            result, msg = kapacitor.update_template(template_id,body)
        except Exception as e:
            msg = f"Could not update the channel status: {template_id}; exception: {e}"

        logger.debug(str(result))
        return utils.ok(result=meta.strip_meta(result), msg=msg)

    def delete(self, template_id):
        logger.debug("top of DELETE /channels/{channel_id}")

class InfluxResource(Resource):

    #Expect fields[] parameters
    #EXAMPLE: fields[]={"inst":1}&fields[]={"var":1}
    def get(self):
        logger.debug(request.args)
        field_list = request.args.getlist('fields[]')
        #expects instrument_id=1&vars[]={"somename":1.0}&vars[]={"other":2.0} in the request.args
        resp = influx.query_measurments(field_list)
        logger.debug(resp)
        return resp

    def post(self):
        logger.debug(request.args)
        #expects instrument_id=1&vars[]={"somename":1.0}&vars[]={"other":2.0} in the request.args
        resp = influx.create_measurement(request.args.get('site_id'), request.args.get('inst_id'), request.args.get('var_id'),  float(request.args.get('value')), request.args.get('timestamp'), )
        logger.debug(resp)
        return resp
