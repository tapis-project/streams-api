from flask import g, request

from common import auth
from common import errors as common_errors
from common.config import conf

# get the logger instance -
from common.logs import get_logger
logger = get_logger(__name__)

def authn_and_authz():
    """
    Entry point for checking authentication and authorization for all requests to the authenticator.
    :return:
    """
    authentication()
    authorization()

def authentication():
    """
    Entry point for checking authentication for all requests to the authenticator.
    :return:
    """
    # The tenants API has both public endpoints that do not require a token as well as endpoints that require
    # authorization.
    # we always try to call the primary tapis authentication function to add authentication information to the
    # thread-local. If it fails due to a missing token, we then check if there is a p
    if conf.local_dev == 'true':
        return true
    else:
        try:
            auth.authentication()
        except common_errors.NoTokenError as e:
            logger.debug(f"Caught NoTokenError: {e}")
            g.no_token = True
            # for retrieval and informational methods, allow the request (with possibly limited information)

            if request.method == 'GET' or request.method == 'PUT' or request.method == 'DELETE' or request.method == 'GET' or request.method == 'HEAD' or request.method == 'POST':
                return True
            raise e




def authorization():
    """
    Entry point for checking authorization for all requests to the authenticator.
    :return:
    """
    # todo - Call security kernel to check if user is authorized for the request.
    #
    return True
