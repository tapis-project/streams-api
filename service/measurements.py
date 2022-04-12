import enum
import requests
import json
from flask import g, Flask
from common.config import conf
from common import auth
import datetime
app = Flask(__name__)

from common import utils, errors
from service import auth
from service import chords
# get the logger instance -
from common.logs import get_logger
logger = get_logger(__name__)

from service import influx

t = auth.t

def fetch_measurement_dataframe(instrument, request):
    influx_query_input = [{"inst":str(instrument['chords_id'])}]
    if request.args.get('start_date'):
        influx_query_input.append({"start_date": request.args.get('start_date')})
    if request.args.get('end_date'):
        influx_query_input.append({"end_date": request.args.get('end_date')})    
    if request.args.get('limit'):
        influx_query_input.append({"limit": request.args.get('limit')}) 
    if request.args.get('offset'):
        influx_query_input.append({"offset": request.args.get('offset')}) 
    return influx.query_measurments( influx_query_input)
