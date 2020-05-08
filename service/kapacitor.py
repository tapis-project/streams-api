import datetime
import enum
import requests
import json
from flask import g, Flask
from common.config import conf
app = Flask(__name__)

from common import utils, errors
# get the logger instance -
from common.logs import get_logger
logger = get_logger(__name__)


def create_channel():
    return True

def list_channels():
    return True

def get_channel():
    return true

def update_channel():
    return True

def remove_channel():
    return True

################### ALERT ############################################
def create_alert():
    return True

def get_alert():
    return True

def list_alerts():
    return True

def update_alert():
    return True

def remove_alert():
    return True

################### TEMPLATE ##########################################

def create_template():
    return True

def get_template():
    return True

def list_templates():
    return True

def update_template():
    return True

def remove_template():
    return True
