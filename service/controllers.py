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
        return ""

    def post(self):
        return ""

class ProjectResource(Resource):
    """
    Work with Project objects
    """

    def get(self, project_id):
        return ""

    def put(self, project_id):
        return ""

    def delete(self, project_id):
        return ""

class SitesResource(Resource):
    """
    Work with Sites objects
    """

    #TODO metadata integration - need to use query, limit and offset
    def get(self, project_id):
        resp = meta.list_sites(project_id)
        #resp = chords.list_sites()
        logger.debug(resp)
        return resp

    def post(self, project_id):
        #need to add check for project permission & project exists before chords insertion
        logger.debug('omg')
        logger.debug(request.json)
        body = request.json
        postSite = ChordsSite("",body['site_name'],
                                body['latitude'],
                                body['longitude'],
                                body['elevation'],
                                body['description'])
        resp = chords.create_site(postSite)
        if resp['status'] == 201:
            meta_resp = meta.create_site(project_id, resp['results']['id'],body)
            #resp['results']=meta_resp['results']
            resp['status'] = meta_resp['status']
            logger.debug(meta_resp['status'])
        logger.debug(resp)
        return resp



class SiteResource(Resource):
    """
    Work with Sites objects
    """

    def get(self, project_id, site_id):
        #resp = chords.get_site(site_id)
        resp = meta.get_site(project_id,site_id)
        logger.debug(resp)
        return resp

    def put(self, project_id, site_id):
        body = request.json
        putSite = ChordsSite(site_id,
                              body['site_name'],
                              body['latitude'],
                              body['longitude'],
                              body['elevation'],
                              body['description'])
        resp = chords.update_site(site_id, putSite)
        logger.debug(resp)
        return resp

    def delete(self, project_id, site_id):
        resp = chords.delete_site(site_id)
        logger.debug(resp)
        return resp

class InstrumentsResource(Resource):
    """
    Work with Instruments objects
    """

    def get(self,project_id,site_id):
        resp = chords.list_instruments()
        logger.debug(resp)
        return resp

    #TODO support bulk create operations
    def post(self, project_id, site_id):
        logger.debug(type(request.json))
        logger.debug(request.json)
        #TODO loop through list objects to support buld operations
        if type(request.json) is dict:
            body = request.json
        else:
            body = request.json[0]
        logger.debug('before ChordsInstrument assignment')
        #id, site_id, name, sensor_id, topic_category_id, description, display_points, plot_offset_value, plot_offset_units, sample_rate_seconds):

        postInst = ChordsIntrument("",site_id,
                                    body['inst_name'],
                                    "",
                                    "1",
                                    body['inst_description'],
                                    "120",
                                    "1",
                                    "weeks",
                                    "60")
        logger.debug('after ChordsInstrument assignment')
        resp = chords.create_instrument(postInst)
        logger.debug(resp)
        return resp


class InstrumentResource(Resource):
    """
    Work with Instruments objects
    """

    def get(self, project_id, site_id, instrument_id):
        resp = chords.get_instrument(instrument_id)
        logger.debug(resp)
        return resp

    def put(self, project_id, site_id, instrument_id):
        logger.debug(type(request.json))
        logger.debug(request.json)
        #TODO loop through list objects to support buld operations
        if type(request.json) is dict:
            body = request.json
        else:
            body = request.json[0]
        putInst = ChordsIntrument(instrument_id,site_id,
                                    body['inst_name'],
                                    "",
                                    "",
                                    body['inst_description'],
                                    "",
                                    "",
                                    "",
                                    "")
        resp = chords.update_instrument(instrument_id, putInst)
        logger.debug(resp)
        return resp

    def delete(self, project_id, site_id, instrument_id):
        resp = chords.delete_instrument(instrument_id)
        logger.debug(resp)
        return resp

class VariablesResource(Resource):
    """
    Work with Variables objects
    """

    def get(self, project_id, site_id, instrument_id):
        resp = chords.list_variables()
        logger.debug(resp)
        return resp


    def post(self, project_id, site_id, instrument_id):
        logger.debug(type(request.json))
        logger.debug(request.json)
        #TODO loop through list objects to support buld operations
        if type(request.json) is dict:
            body = request.json
        else:
            body = request.json[0]
        # id, name, instrument_id, shortname, commit
        postInst = ChordsVariable("",instrument_id,
                                    body['var_name'],
                                    body['shortname'],
                                    "")
        logger.debug(postInst)
        resp = chords.create_variable(postInst)
        logger.debug(resp)
        return resp



class VariableResource(Resource):
    """
    Work with Variables objects
    """

    def get(self, project_id, site_id, instrument_id, variable_id):
        resp = chords.get_variable(variable_id)
        logger.debug(resp)
        return resp

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
        resp = chords.update_variable(variable_id,putInst)
        logger.debug(resp)
        return resp

    def delete(self, project_id, site_id, instrument_id, variable_id):
        resp = chords.delete_variable(variable_id)
        logger.debug(resp)
        return resp

class MeasurementsResource(Resource):
    """
    Work with Measurements objects
    """
    #
    def get(self, project_id, site_id, instrument_id):
        logger.debug("top of GET /measurements")
        resp = chords.get_measurements(instrument_id)
        logger.debug(resp)
        return resp

    #at the moment expects some like
    #http://localhost:5000/v3/streams/measurements?instrument_id=1&vars[]={"somename":1.0}&vars[]={"other":2.0}
    #will need to adjust when openAPI def is final for measurement
    def post(self, project_id, site_id, instrument_id):
        body = request.json
        logger.debug(body)
        #expects instrument_id=1&vars[]={"somename":1.0}&vars[]={"other":2.0} in the request.args
        resp = chords.create_measurement(body)
        logger.debug(resp)
        return resp


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

class StreamsResource(Resource):
    """
    Work with Streams objects
    """

    def get(self):
        logger.debug("top of GET /streams")

    def post(self):
        logger.debug("top of POST /streams")


class StreamResource(Resource):
    """
    Work with Streams objects
    """

    def get(self, stream_id):
        logger.debug("top of GET /streams/{stream_id}")

    def put(self, stream_id):
        logger.debug("top of PUT /streams/{stream_id}")

    def delete(self, stream_id):
        logger.debug("top of DELETE /streams/{stream_id}")

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
