import datetime
from flask import request
from flask_restful import Resource
from openapi_core.shortcuts import RequestValidator
from openapi_core.wrappers.flask import FlaskOpenAPIRequest
# import psycopg2
#import sqlalchemy
import chords
import influx
from models import ChordsSite
from common import utils, errors
#from service.models import db, LDAPConnection, TenantOwner, Tenant

# get the logger instance -
from common.logs import get_logger
logger = get_logger(__name__)


class SitesResource(Resource):
    """
    Work with Sites objects
    """

    def get(self):
        resp = chords.list_sites()
        logger.debug(resp)
        return resp

    def post(self):
        postSite = ChordsSite("",request.args.get('name'),
                              request.args.get('lat'),
                              request.args.get('long'),
                              request.args.get('elevation'),
                              request.args.get('description'))
        resp = chords.create_site(postSite)
        logger.debug(resp)
        return resp



class SiteResource(Resource):
    """
    Work with Sites objects
    """

    def get(self, site_id):
        resp = chords.get_site(site_id)
        logger.debug(resp)
        return resp

    def put(self, site_id):
        putSite = ChordsSite(site_id,
                              request.args.get('name'),
                              request.args.get('lat'),
                              request.args.get('long'),
                              request.args.get('elevation'),
                              request.args.get('description'))
        resp = chords.update_site(site_id, putSite)
        logger.debug(resp)
        return resp

    def delete(self, site_id):
        resp = chords.delete_site(site_id)
        logger.debug(resp)
        return resp

class InstrumentsResource(Resource):
    """
    Work with Instruments objects
    """

    def get(self):
        resp = chords.list_instruments()
        logger.debug(resp)
        return resp

    def post(self):
        resp = chords.create_instrument(request.args)
        logger.debug(resp)
        return resp


class InstrumentResource(Resource):
    """
    Work with Instruments objects
    """

    def get(self, instrument_id):
        resp = chords.get_instrument(instrument_id)
        logger.debug(resp)
        return resp

    def put(self, instrument_id):
        resp = chords.update_instrument(instrument_id, request.args)
        logger.debug(resp)
        return resp

    def delete(self, instrument_id):
        resp = chords.delete_instrument(instrument_id)
        logger.debug(resp)
        return resp

class VariablesResource(Resource):
    """
    Work with Variables objects
    """

    def get(self):
        resp = chords.list_variables()
        logger.debug(resp)
        return resp


    def post(self):
        resp = chords.create_variable(request.args)
        logger.debug(resp)
        return resp



class VariableResource(Resource):
    """
    Work with Variables objects
    """

    def get(self, variable_id):
        resp = chords.get_variable(variable_id)
        logger.debug(resp)
        return resp

    def put(self, variable_id):
        resp = chords.update_variable(variable_id,request.args)
        logger.debug(resp)
        return resp

    def delete(self, variable_id):
        resp = chords.delete_variable(variable_id)
        logger.debug(resp)
        return resp

class MeasurementsResource(Resource):
    """
    Work with Measurements objects
    """
    #
    def get(self):
        logger.debug("top of GET /measurements")

    #at the moment expects some like
    #http://localhost:5000/v3/streams/measurements?instrument_id=1&vars[]={"somename":1.0}&vars[]={"other":2.0}
    #will need to adjust when openAPI def is final for measurement
    def post(self):
        logger.debug(request.args)
        #expects instrument_id=1&vars[]={"somename":1.0}&vars[]={"other":2.0} in the request.args
        resp = chords.create_measurement(request.args)
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
