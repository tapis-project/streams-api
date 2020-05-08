import datetime
from flask import request
from flask_restful import Resource
from openapi_core.shortcuts import RequestValidator
from openapi_core.wrappers.flask import FlaskOpenAPIRequest
# import psycopg2
#import sqlalchemy
import chords
import influx
import meta
import kapacitor
from models import ChordsSite, ChordsIntrument, ChordsVariable
from common import utils, errors
#from service.models import db, LDAPConnection, TenantOwner, Tenant

# get the logger instance -
from common.logs import get_logger
logger = get_logger(__name__)




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
        proj_result, msg = meta.create_project(body)
        logger.debug(proj_result)
        result = meta.strip_meta(proj_result)
        #resp['status'] = result['status']
        #logger.debug(meta_resp['status'])
        #logger.debug(resp)
        return utils.ok(result, msg=msg)

class ProjectResource(Resource):
    """
    Work with Project objects
    """

    def get(self, project_id):
        proj_result, msg = meta.get_project(project_id)
        result = meta.strip_meta(proj_result)
        logger.debug(result)
        return utils.ok(result=result, msg=msg)

    def put(self, project_id):
        body = request.json
        proj_result, msg = meta.update_project(project_id, body)
        result = meta.strip_meta(proj_result)
        return utils.ok(result=result, msg=msg)

    def delete(self, project_id):
        return ""

class SitesResource(Resource):
    """
    Work with Sites objects
    """

    #TODO metadata integration - need to use query, limit and offset
    def get(self, project_id):
        site_result, msg = meta.list_sites(project_id)
        result = meta.strip_meta_list(site_result)
        return utils.ok(result=result,msg=msg)


    def post(self, project_id):
        # validator = RequestValidator(utils.spec)
        # result = validator.validate(FlaskOpenAPIRequest(request))
        # if result.errors:
        #     raise errors.ResourceError(msg=f'Invalid POST data: {result.errors}.')
        # validated_params = result.parameters
        # validated_body = result.body
        # logger.debug(f"validated_body: {dir(validated_body)}")

        #need to add check for project permission & project exists before chords insertion
        logger.debug('omg')
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



class SiteResource(Resource):
    """
    Work with Sites objects
    """

    def get(self, project_id, site_id):
        site_result, msg = meta.get_site(project_id,site_id)
        result = meta.strip_meta(site_result)
        logger.debug(result)
        return utils.ok(result=result, msg=msg)

    def put(self, project_id, site_id):
        body = request.json
        putSite = ChordsSite(site_id,
                              body['site_name'],
                              body['latitude'],
                              body['longitude'],
                              body['elevation'],
                              body['description'])
        site_result, msg = meta.update_site(project_id, site_id, body)
        result = meta.strip_meta(site_result)
        chord_result, chord_msg = chords.update_site(site_id, putSite)
        return utils.ok(result=result, msg=msg)

    def delete(self, project_id, site_id):
        result, msg = chords.delete_site(site_id)
        logger.debug(msg)
        return utils.ok(result='null', msg=f'Site {site_id} deleted.')


class InstrumentsResource(Resource):
    """
    Work with Instruments objects
    """
    def get(self,project_id,site_id):
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

    #TODO support bulk create operations
    def post(self, project_id, site_id):
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


class InstrumentResource(Resource):
    """
    Work with Instruments objects
    """
    def get(self, project_id, site_id, instrument_id):
        #result,msg = chords.get_instrument(instrument_id)
        result,msg = meta.get_instrument(project_id, site_id,instrument_id)
        return utils.ok(result=result, msg=msg)


    def put(self, project_id, site_id, instrument_id):
        logger.debug(type(request.json))
        logger.debug(request.json)
        #TODO loop through list objects to support buld operations
        if type(request.json) is dict:
            body = request.json
        else:
            body = request.json[0]

        result, msg = meta.update_instrument(project_id, site_id, instrument_id, body)
        putInst = ChordsIntrument(int(result['chords_id']),site_id,
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


    def delete(self, project_id, site_id, instrument_id):
        chord_result,chord_msg = chords.delete_instrument(instrument_id)
        result, msg = meta.update_instrument(project_id, site_id, instrument_id, {},True)
        return utils.ok(result="null", msg=msg)


class VariablesResource(Resource):
    """
    Work with Variables objects
    """

    def get(self, project_id, site_id, instrument_id):
        #result,msg = chords.list_variables()
        result, msg = meta.list_variables(project_id, site_id, instrument_id)
        logger.debug(instrument_id)
        return utils.ok(result=result, msg=msg)


    def post(self, project_id, site_id, instrument_id):
        #logger.debug(type(request.json))
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


class VariableResource(Resource):
    """
    Work with Variables objects
    """
    def get(self, project_id, site_id, instrument_id, variable_id):
        chords_result,chords_msg = chords.get_variable(variable_id)
        result, msg = meta.get_variable(project_id, site_id, instrument_id, variable_id)
        logger.debug(result)
        return utils.ok(result=result, msg=msg)


    def put(self,project_id, site_id, instrument_id,  variable_id):
        logger.debug(type(request.json))
        logger.debug(request.json)
        #TODO loop through list objects to support buld operations
        if type(request.json) is dict:
            body = request.json
        else:
            body = request.json[0]
        # id, name, instrument_id, shortname, commit
        putInst = ChordsVariable(variable_id,instrument_id,
                                    body['var_name'],
                                    body['shortname'],
                                    "")
        logger.debug(putInst)
        chord_result,chord_msg = chords.update_variable(variable_id,putInst)
        result, msg = meta.update_variable(project_id, site_id, instrument_id, variable_id, body)
        logger.debug(result)
        return utils.ok(result=result, msg=msg)

    def delete(self, project_id, site_id, instrument_id, variable_id):
        result,msg = chords.delete_variable(variable_id)
        result, msg = meta.update_variable(project_id, site_id, instrument_id, variable_id, {},True)
        logger.debug(result)
        return utils.ok(result=result, msg=msg)


class MeasurementsWriteResource(Resource):
    #at the moment expects some like
    #http://localhost:5000/v3/streams/measurements?instrument_id=1&vars[]={"somename":1.0}&vars[]={"other":2.0}
    #will need to adjust when openAPI def is final for measurement
    def post(self):
        body = request.json
        logger.debug(body)
        if 'inst_id' in body:
            result = meta.fetch_instrument_index(body['inst_id'])
            logger.debug(result)
            if len(result) > 0:
                #check SK
                logger.debug("YES")
                logger.debug(result[0]['chords_inst_id'])

                resp = chords.create_measurement(result[0]['chords_inst_id'], body)
                logger.debug(resp)
        return resp


class MeasurementsResource(Resource):
    """
    Work with Measurements objects
    """
    #
    def get(self, project_id, site_id, instrument_id):
        logger.debug("top of GET /measurements")
        inst_result = meta.get_instrument(project_id,site_id,instrument_id)
        logger.debug(inst_result)
        if len(inst_result) > 0:
            result,msg = chords.get_measurements(str(inst_result[0]['chords_inst_id']))
            logger.debug(result)
        return utils.ok(result=result, msg=msg)

class MeasurementResource(Resource):
    """
    Work with Measurements objects
    """

    def get(self, measurement_id):
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

    def post(self):
        logger.debug("top of POST /channels")
        body = request.json
        result, msg = kapacitor.create_channel(body)
        return utils.ok(result=result, msg=msg)
        


class ChannelResource(Resource):
    """
    Work with Streams objects
    """

    def get(self, channel_id):
        logger.debug("top of GET /channels/{channel_id}")

    def put(self, channel_id):
        logger.debug("top of PUT /channels/{channel_id}")

    def delete(self, channel_id):
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

#class ChannelResource(Resource):


#class ChannelsResource(Resource):
