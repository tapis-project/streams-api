import datetime
from flask import request
from flask_restful import Resource
from openapi_core.shortcuts import RequestValidator
from openapi_core.wrappers.flask import FlaskOpenAPIRequest
# import psycopg2
import sqlalchemy

from common import utils, errors
from service.models import db, LDAPConnection, TenantOwner, Tenant

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
