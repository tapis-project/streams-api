import datetime
import enum
import requests
import json
from flask import g, Flask
#from models import ChordsSite, ChordsIntrument, ChordsVariable, ChordsMeasurement
from common.config import conf
app = Flask(__name__)

from common import utils, errors
# get the logger instance -
from common.logs import get_logger
logger = get_logger(__name__)


#Sites endpoints supported in chords

#Can fetch all the site in JSON from CHORDS
#TODO - will need to filter the output based on the user permission either in here
# or post the return
def list_sites():
    #GET get a site from chords service
    logger.debug("IN CHORDS LIST SITES")
    chords_uri = conf.chords_url+"/sites.json";
    getData = {'email':conf.chords_user_email,
               'api_key': conf.chords_api_key}
    headers = {
        'Content-Type':'application/x-www-form-urlencoded'
    }
    res = requests.get(chords_uri, data=getData, headers=headers,verify=False)
    resp = json.loads(res.content)
    return resp

#fetch a specific site by its id from CHORDS
def get_site(id):
    #GET get a site from chords service
    chords_uri = conf.chords_url+"/sites/"+id+".json";
    getData = {'email':conf.chords_user_email,
               'api_key': conf.chords_api_key,}
    headers = {
        'Content-Type':'application/x-www-form-urlencoded'
    }
    res = requests.get(chords_uri, data=getData, headers=headers,verify=False)
    resp = json.loads(res.content)
    return resp

#create a new site in CHORDS
def create_site(req_args):
    #TODO validate the site has all properties requirement and fields are correct
    chords_uri = conf.chords_url+"/sites.json"
    postData = {'email':conf.chords_user_email,
                'api_key': conf.chords_api_key,
                'site[name]':req_args.get('name'),
                'site[lat]': req_args.get('lat'),
                'site[lon]': req_args.get('long'),
                'site[elevation]': req_args.get('elevation'),
                }
    headers = {
         'Content-Type':'application/x-www-form-urlencoded'
    }
    res = requests.post(chords_uri, data=postData, headers=headers,verify=False)
    logger.debug(res.content)
    resp =json.loads(res.content)
    return resp
#
# #update a site in CHORDS
def update_site(id, req_args):
    #TODO validate the site has all properties requirement and fields are correct
    chords_uri = conf.chords_url+"/sites/"+id+".json"
    postData = {'email':conf.chords_user_email,
                'api_key': conf.chords_api_key,
                'site[name]':req_args.get('name'),
                'site[lat]': req_args.get('lat'),
                'site[lon]': req_args.get('long'),
                'site[elevation]': req_args.get('elevation'),
                }
    headers = {
         'Content-Type':'application/x-www-form-urlencoded'
    }
    res = requests.put(chords_uri, data=postData, headers=headers,verify=False)
    logger.debug(res.content)
    resp =json.loads(res.content)
    return resp
#
# #delete a site from CHORDS
def delete_site(id):
    chords_uri = conf.chords_url+"/sites/"+id+".json";
    deleteData = {'email':conf.chords_user_email,
                  'api_key': conf.chords_api_key}
    headers = {
        'Content-Type':'application/x-www-form-urlencoded'
    }
    res = requests.delete(chords_uri, data=deleteData, headers=headers,verify=False)
    logger.debug(res.status_code)
    #Chords returns a 204 so we can only return the response
    resp=res.status_code
    return resp

#Instruments endpoints supported in chords

#Can fetch all the instruments in JSON from CHORDS
#TODO - will need to filter the output based on the user permission either in here
# or post the return
def list_instruments():
    #GET get a instrument from chords service
    chords_uri = conf.chords_url+"/instruments.json";
    getData = {'email':conf.chords_user_email,
               'api_key': conf.chords_api_key}
    headers = {
        'Content-Type':'application/x-www-form-urlencoded'
    }
    res = requests.get(chords_uri, data=getData, headers=headers,verify=False)
    logger.debug(res.content)
    resp = json.loads(res.content)
    return resp

#fetch a specific instrument by its id from CHORDS
def get_instrument(id):
    #GET get a instrument from chords service
    chords_uri = conf.chords_url+"/instruments/"+id+".json";
    getData = {'email':conf.chords_user_email,
               'api_key': conf.chords_api_key}
    headers = {
        'Content-Type':'application/x-www-form-urlencoded'
    }
    res = requests.get(chords_uri, data=getData, headers=headers,verify=False)
    resp = json.loads(res.content)
    return resp

#create a new instrument in CHORDS
def create_instrument(req_args):
    #TODO validate the instrument has all properties requirement and fields are correct
    chords_uri = conf.chords_url+"/instruments.json";
    postData = {'email':conf.chords_user_email,
                'api_key': conf.chords_api_key,
                'instrument[site_id]':req_args.get('site_id'),
                'instrument[name]': req_args.get('name'),
                'instrument[sensor_id]': req_args.get('sensor_id'),
                'instrument[topic_category_id]': req_args.get('topic_category_id'),
                'instrument[description]': req_args.get('description'),
                'instrument[display_points]': req_args.get('display_points'),
                'instrument[plot_offset_value]': req_args.get('plot_offset_value'),
                'instrument[plot_offset_units]': req_args.get('plot_offset_units'),
                'instrument[sample_rate_seconds]': req_args.get('sample_rate_seconds')
                }
    headers = {
        'Content-Type':'application/x-www-form-urlencoded'
    }
    res = requests.post(chords_uri, data=postData, headers=headers,verify=False)
    logger.debug(res.content)
    resp = json.loads(res.content)
    return resp

#update a instrument in CHORDS
def update_instrument(id, req_args):
    #TODO validate the instrument has all properties requirement and fields are correct
    chords_uri = conf.chords_url+"/instruments/"+id+".json";
    putData = {'email':conf.chords_user_email,
                'api_key': conf.chords_api_key,
                'instrument[site_id]':req_args.get('site_id'),
                'instrument[name]': req_args.get('name'),
                'instrument[sensor_id]': req_args.get('sensor_id'),
                'instrument[topic_category_id]': req_args.get('topic_category_id'),
                'instrument[description]': req_args.get('description'),
                'instrument[display_points]': req_args.get('display_points'),
                'instrument[plot_offset_value]': req_args.get('plot_offset_value'),
                'instrument[plot_offset_units]': req_args.get('plot_offset_units'),
                'instrument[sample_rate_seconds]': req_args.get('sample_rate_seconds')
                }
    headers = {
        'Content-Type':'application/x-www-form-urlencoded'
    }
    res = requests.put(chords_uri, data=putData, headers=headers,verify=False)
    resp = json.loads(res.content)
    return resp

#delete a instrument from CHORDS
def delete_instrument(id):
    chords_uri = conf.chords_url+"/instruments/"+id+".json";
    deleteData = {'email':conf.chords_user_email,
                  'api_key': conf.chords_api_key}
    headers = {
        'Content-Type':'application/x-www-form-urlencoded'
    }
    res = requests.delete(chords_uri, data=deleteData, headers=headers,verify=False)
    logger.debug(res.status_code)
    resp={'msg':res.status_code}
    #resp = json.loads(res.content)
    return resp

# #variable endpoints supported in chords
#
#Can fetch all the variables in JSON from CHORDS
#TODO - will need to filter the output based on the user permission either in here
# or post the return
def list_variables():
    #GET get all variables from chords service
    chords_uri = conf.chords_url+"/vars.json";
    getData = {'email':conf.chords_user_email,
                  'api_key': conf.chords_api_key}
    headers = {
        'Content-Type':'application/x-www-form-urlencoded'
    }
    res = requests.get(chords_uri, data=getData, headers=headers,verify=False)
    resp = json.loads(res.content)
    return resp

#fetch a specific variable by its id from CHORDS
def get_variable(id):
    #GET get a instrument from chords service
    chords_uri = conf.chords_url+"/vars/"+id+".json";
    getData = {'email':conf.chords_user_email,
                  'api_key': conf.chords_api_key}
    headers = {
        'Content-Type':'application/x-www-form-urlencoded'
    }
    res = requests.get(chords_uri, data=getData, headers=headers,verify=False)
    resp = json.loads(res.content)
    return resp

#create a new variable in CHORDS
def create_variable(req_args):
    #TODO validate the variable has all properties requirement and fields are correct
    chords_uri = conf.chords_url+"/vars.json";
    postData = {'email':conf.chords_user_email,
                  'api_key': conf.chords_api_key,
                  'var[name]':req_args.get('name'),
                  'var[instrument_id]': req_args.get('instrument_id'),
                  'var[shortname]': req_args.get('shortname'),
                  'var[commit]': 'Create Variable'}
    headers = {
        'Content-Type':'application/x-www-form-urlencoded'
    }
    res = requests.post(chords_uri, data=postData, headers=headers,verify=False)
    resp = json.loads(res.content)
    return resp

#update a variable in CHORDS
def update_variable(id,req_args):
    #TODO validate the variable has all properties requirement and fields are correct
    chords_uri = conf.chords_url+"/vars/"+id+".json";
    putData = {'email':conf.chords_user_email,
                  'api_key': conf.chords_api_key,
                  'var[name]':req_args.get('name'),
                  'var[instrument_id]': req_args.get('instrument_id'),
                  'var[shortname]': req_args.get('shortname')
                  }
    headers = {
        'Content-Type':'application/x-www-form-urlencoded'
    }
    res = requests.put(chords_uri, data=putData, headers=headers,verify=False)
    resp = json.loads(res.content)
    return resp

#delete a variable from CHORDS
def delete_variable(id):
    chords_uri =    conf.chords_url+"/vars/"+id+".json";
    deleteData={'email':conf.chords_user_email,
                  'api_key': conf.chords_api_key}
    headers = {
        'Content-Type':'application/x-www-form-urlencoded'
    }
    res = requests.delete(chords_uri, data=deleteData, headers=headers,verify=False)
    logger.debug(res.status_code)
    resp={'msg':res.status_code}
    return resp
#
# #measurement endpoints supported in chords
#
#Can fetch all the measurments in JSON from CHORDS
#TODO - will need to filter the output based on the user permission either in here
# or post the return
def get_measurements():
    #GET get all variables from chords service
    chords_uri = "http://"+conf.chords_url+"api/v1/data.json";
    #start, end, instruments
    getData = {'email':conf.chords_user_email,
                  'api_key': conf.chords_api_key}
    headers = {
        'Content-Type':'application/x-www-form-urlencoded'
    }
    res = requests.get(chords_uri, data=getData, headers=headers,verify=False)
    resp = json.loads(res.content)
    return resp
#
#create a new measurement in CHORDS
def create_measurement(req_args):
    #TODO validate the measurement has all properties requirement and fields are correct
    chords_uri = conf.chords_url+"/measurements/url_create.json?";
    #need api_key, instrument_id, at and variable shortnames
    #measurement_data =Object.assign({}, {email:chords_email,api_key: chords_api_token,instrument_id: response2['result']['value']['chords_id'], at: req.query.at || new Date().toISOString()},req.query.vars)
    postData = {'email':conf.chords_user_email,
                'api_key': conf.chords_api_key,
                'instrument_id' : req_args.get('instrument_id')
                }
    for itm in req_args.getlist('vars[]'):
        vars = json.loads(itm)
        for k in vars:
            postData[k]=vars[k]
    logger.debug(postData)
    headers = {
        'Content-Type':'application/x-www-form-urlencoded'
    }
    #CHORDS uses a GET method to create a new measurement
    res = requests.get(chords_uri, data=postData, headers=headers,verify=False)
    logger.debug(res.content)
    resp = json.loads(res.content)
    return resp
#
#
# #delete a variable from CHORDS
# def delete_measurement(measurement_id):
#     chords_uri = "http://"+conf.chords_url+"/measurement/"+id;
#     headers = {
#         'Content-Type': 'application/json',
#     }
#     res = requests.delete(chords_uri, headers=headers,verify=False)
#     resp = json.loads(res.content)
#     return resp
