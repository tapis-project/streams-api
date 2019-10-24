import datetime
from flask import request
from flask_restful import Resource
from openapi_core.shortcuts import RequestValidator
from openapi_core.wrappers.flask import FlaskOpenAPIRequest
# import psycopg2
import sqlalchemy

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
        logger.debug("top of GET /sites")

    def post(self):
        logger.debug("top of POST /sites")


class SiteResource(Resource):
    """
    Work with Sites objects
    """

    def get(self, site_id):
        logger.debug("top of GET /sites/{site_id}")

    def put(self, site_id):
        logger.debug("top of PUT /sites/{site_id}")

    def delete(self, site_id):
        logger.debug("top of DELETE /sites/{site_id}")

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
