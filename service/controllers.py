import datetime
from flask import request
from flask_restful import Resource
from openapi_core.shortcuts import RequestValidator
from openapi_core.wrappers.flask import FlaskOpenAPIRequest
# import psycopg2
#import sqlalchemy
import chords
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
        resp = chords.fetch_sites()
        logger.debug(resp)
        return resp

    def post(self):
        logger.debug(request.args.get('name'))
        resp = chords.create_site(request.args.get('name'))
        logger.debug(resp)
        return resp


class SiteResource(Resource):
    """
    Work with Sites objects
    """

    def get(self, site_id):
        resp = chords.fetch_site(site_id)
        logger.debug(resp)
        return resp

    def put(self, site_id):
        resp = chords.update_site(site_id)
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
        logger.debug("top of GET /instruments")

    def post(self):
        logger.debug("top of POST /instruments")


class InstrumentResource(Resource):
    """
    Work with Instruments objects
    """

    def get(self, instrument_id):
        logger.debug("top of GET /instruments/{instrument_id}")

    def put(self, instrument_id):
        logger.debug("top of PUT /instruments/{instrument_id}")

    def delete(self, instrument_id):
        logger.debug("top of DELETE /instruments/{instrument_id}")

class VariablesResource(Resource):
    """
    Work with Variables objects
    """

    def get(self):
        logger.debug("top of GET /variables")

    def post(self):
        logger.debug("top of POST /variables")


class VariableResource(Resource):
    """
    Work with Variables objects
    """

    def get(self, variable_id):
        logger.debug("top of GET /variables/{variable_id}")

    def put(self, variable_id):
        logger.debug("top of PUT /variables/{variable_id}")

    def delete(self, variable_id):
        logger.debug("top of DELETE /variables/{variable_id}")

class MeasurementsResource(Resource):
    """
    Work with Measurements objects
    """

    def get(self):
        logger.debug("top of GET /measurements")

    def post(self):
        logger.debug("top of POST /measurements")


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
