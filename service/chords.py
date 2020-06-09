import datetime
import enum
import requests
import json
from flask import g, Flask
from models import ChordsSite, ChordsIntrument, ChordsVariable#, ChordsMeasurement
from common.config import conf
app = Flask(__name__)

from common import utils, errors
# get the logger instance -
from common.logs import get_logger
logger = get_logger(__name__)

def create_get_request(path):
    chords_uri = conf.chords_url + path;
    getData = {'email': conf.chords_user_email,
               'api_key': conf.chords_api_key}
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    res = requests.get(chords_uri, data=getData, headers=headers, verify=False)
    logger.debug(res.content)
    return res

def create_post_request(path,postData):
    chords_uri = conf.chords_url + path;
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    res = requests.post(chords_uri, data=postData, headers=headers,verify=False)
    logger.debug(res.content)
    return res

def create_put_request(path,postData):
    chords_uri = conf.chords_url + path;
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    res = requests.put(chords_uri, data=postData, headers=headers, verify=False)
    logger.debug(res.content)
    return res

def create_delete_request(path):
    chords_uri = conf.chords_url + path;
    deleteData = {'email': conf.chords_user_email,
                 'api_key': conf.chords_api_key}
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    res = requests.delete(chords_uri, data=deleteData, headers=headers, verify=False)
    logger.debug(res.content)
    return res

#Sites endpoints supported in chords

#Can fetch all the site in JSON from CHORDS
#TODO - will need to filter the output based on the user permission either in here
# or post  return of results
def list_sites():
    #GET get a site from chords service
    res = create_get_request("/sites.json")
    if (res.status_code == 200):
        message = "Sites found"
    else:
        raise errors.ResourceError(msg=f'No Site found')
    logger.debug(message)
    logger.debug(res)
    return json.loads(res.content.decode('utf-8')),message

#fetch a specific site by its id from CHORDS
def get_site(id):
    #GET get a site from chords service
    res = create_get_request("/sites/"+id+".json");
    if (res.status_code == 200):
        message = "Site found"
    else:
        raise errors.ResourceError(msg=f'No Site found')
    logger.debug(message)
    logger.debug(res)
    return json.loads(res.content.decode('utf-8')), message


#create a new site in CHORDS
def create_site(site:ChordsSite):
        # TODO validate the site has all properties requirement and fields are correct
    postData = {'email': conf.chords_user_email,
                'api_key': conf.chords_api_key,
                'site[name]': site.name,
                'site[lat]': site.lat,
                'site[lon]': site.long,
                'site[elevation]': site.elevation
                }
    logger.debug(postData)
    res = create_post_request("/sites.json",postData)
    logger.debug(res.content)
    if (res.status_code == 201):
       message = "Site created"
    else:
        logger.debug(res.status_code)
        raise errors.ResourceError(msg=f'Site not created')
    logger.debug(message)
    return json.loads(res.content), message


# #update a site in CHORDS
def update_site(id, site:ChordsSite):
    #TODO validate the site has all properties requirement and fields are correct
    postData = {'email':conf.chords_user_email,
                'api_key': conf.chords_api_key,
                'site[name]':site.name,
                'site[lat]': site.lat,
                'site[lon]': site.long,
                'site[elevation]': site.elevation
                }
    logger.debug(postData)
    path = "/sites/" + id + ".json"
    res = create_put_request(path,postData)
    if (res.status_code == 200):
       message = "Site updated"
    else:
        raise errors.ResourceError(msg=f'Site not updated')
    logger.debug(message)
    logger.debug(res)
    return json.loads(res.content.decode('utf-8')), message


#
# #delete a site from CHORDS
def delete_site(id):
    path = "/sites/"+id+".json";
    res = create_delete_request(path)
    #Chords returns a 204 so we can only return the response
    if (res.status_code == 204):
        message = "Site deleted"
    else:
        raise errors.ResourceError(msg=f'Site not deleted.')
    logger.debug(message)
    logger.debug(res)
    return res.content.decode('utf-8'),message


#Instruments endpoints supported in chords

#Can fetch all the instruments in JSON from CHORDS
#TODO - Fix the bug where it returns error when the site exist and no instruments are
# associated with that site, current implementation returns error, it should just
# return null in the response
def list_instruments():
    #GET get a instrument from chords service
     res = create_get_request("/instruments.json")
     if (res.status_code == 200 ):
        message = "Instrument found"
     else:
         raise errors.ResourceError(msg=f'No instrument found')
     logger.debug(message)
     logger.debug(res)
     return json.loads(res.content.decode('utf-8')), message


#fetch a specific instrument by its id from CHORDS
def get_instrument(id):
    #GET get a instrument from chords service
    res= create_get_request("/instruments/"+id+".json");
    if (res.status_code == 200):
        message = "Instrument found"
    else:
        raise errors.ResourceError(msg=f'No instrument found ')
    logger.debug(message)
    logger.debug(res)
    return json.loads(res.content.decode('utf-8')), message


#create a new instrument in CHORDS
def create_instrument(instrument:ChordsIntrument):
    #TODO validate the instrument has all properties requirement and fields are correct
    postData = {'email':conf.chords_user_email,
                'api_key': conf.chords_api_key,
                'instrument[site_id]':instrument.site_id,
                'instrument[name]':instrument.name,
                #'instrument[sensor_id]': instrument.sensor_id,
                'instrument[topic_category_id]': instrument.topic_category_id,
                'instrument[description]': instrument.description,
                'instrument[display_points]': instrument.display_points,
                'instrument[plot_offset_value]': instrument.plot_offset_value,
                'instrument[plot_offset_units]': instrument.plot_offset_units,
                'instrument[sample_rate_seconds]': instrument.sample_rate_seconds
                }
    logger.debug(postData)
    res = create_post_request("/instruments.json", postData)
    logger.debug(res.content)
    if (res.status_code == 201):
        message = "Instrument created"
    else:
        raise errors.ResourceError(msg=f'Instrument not created')
    logger.debug(message)
    logger.debug(res)
    return json.loads(res.content.decode('utf-8')), message


#update a instrument in CHORDS
def update_instrument(id, instrument:ChordsIntrument):
    #TODO validate the instrument has all properties requirement and fields are cosrrect
    putData = {'email':conf.chords_user_email,
                'api_key': conf.chords_api_key,
                'instrument[site_id]':instrument.site_id,
                'instrument[name]':instrument.name,
                'instrument[topic_category_id]': instrument.topic_category_id,
                'instrument[description]': instrument.description,
                'instrument[display_points]': instrument.display_points,
                'instrument[plot_offset_value]': instrument.plot_offset_value,
                'instrument[plot_offset_units]': instrument.plot_offset_units,
                'instrument[sample_rate_seconds]': instrument.sample_rate_seconds
                }
    logger.debug(putData)
    path = "/instruments/"+id+".json"
    res = create_put_request(path, putData)
    if (res.status_code == 200):
        message = "Instrument updated"
    else:
        raise errors.ResourceError(msg=f'Instrument not updated')
    #logger.debug(message)
    #logger.debug(res)
    return json.loads(res.content.decode('utf-8')), message


#delete a instrument from CHORDS
def delete_instrument(id):
    path = "/instruments/"+id+".json"
    res = create_delete_request(path)
    logger.debug(res.status_code)
    # Chords returns a 204 so we can only return the response
    if (res.status_code == 204):
       message = "Instrument deleted"
    else:
        raise errors.ResourceError(msg=f'Instrument not deleted')
    logger.debug(message)
    logger.debug(res)
    return res.content.decode('utf-8'), message


# #variable endpoints supported in chords
#
#Can fetch all the variables in JSON from CHORDS
#TODO - will need to filter the output based on the user permission either in here
# or post the return
def list_variables():
    #GET get all variables from chords service
    res = create_get_request("/vars.json");
    logger.debug(res.status_code)
    if (res.status_code == 200):
        message = "Variable found"
    else:
        raise errors.ResourceError(msg=f'Variable not found')
    logger.debug(message)
    logger.debug(res)
    return json.loads(res.content.decode('utf-8')), message


#fetch a specific variable by its id from CHORDS
def get_variable(id):
    #GET get a instrument from chords service
    res = create_get_request("/vars/" + id + ".json");
    if (res.status_code == 200):
       message = "Variable found"
    else:
        raise errors.ResourceError(msg=f'Variable not found')
    logger.debug(message)
    logger.debug(res)
    return json.loads(res.content.decode('utf-8')), message


#create a new variable in CHORDS

def create_variable(variable:ChordsVariable):
    #TODO validate the variable has all properties requirement and fields are correct
    postData = {'email':conf.chords_user_email,
                  'api_key': conf.chords_api_key,
                  'var[name]':variable.name,
                  'var[instrument_id]': variable.instrument_id,
                  'var[shortname]': variable.shortname,
                  'var[commit]': 'Create Variable'}
    logger.debug(postData)
    res = create_post_request("/vars.json", postData)
    logger.debug(res.content)
    if (res.status_code == 201):
        message = "Variable created"
    else:
        raise errors.ResourceError(msg=f'Variable not created')
    logger.debug(message)
    logger.debug(res)
    return json.loads(res.content.decode('utf-8')), message



#update a variable in CHORDS
def update_variable(id,variable:ChordsVariable):
    #TODO validate the variable has all properties requirement and fields are correct
    path="/vars/"+id+".json";
    putData = {'email':conf.chords_user_email,
                  'api_key': conf.chords_api_key,
                  'var[name]': variable.name,
                  'var[instrument_id]':  variable.instrument_id,
                  'var[shortname]':  variable.shortname
                  }

    res = create_put_request(path, putData)
    if (res.status_code == 200):
        message = "Instrument updated"
    else:
        raise errors.ResourceError(msg=f'Variable not updated')
    logger.debug(message)
    logger.debug(res)
    return json.loads(res.content.decode('utf-8')), message


#delete a variable from CHORDS
def delete_variable(id):
    path = "/vars/" + id + ".json";
    res = create_delete_request(path)
    logger.debug(res.status_code)
    # Chords returns a 204 so we can only return the response
    if (res.status_code == 204):
        message = "Variable deleted"
    else:
        raise errors.ResourceError(msg=f'Variable not deleted')
    logger.debug(message)
    logger.debug(res)
    return res.content.decode('utf-8'), message

#
# #measurement endpoints supported in chords
#
#Can fetch all the measurments in JSON from CHORDS
#TODO - will need to filter the output based on the user permission either in here
# or post the return
def get_measurements(instrument_id, start="", end="", format="json"):
    #GET get all variables from chords service
    logger.debug("inside chords get measurement")
    if format is None:
        format = "json"
    path="/instruments/"+ instrument_id +"."+format+"?"#"api/v1/data.json";
    #start, end, instruments
    logger.debug(start)
    logger.debug(end)
    if start is not None:
        if len(start) > 0:
            path = path + "&start="+start
    if end is not None:
        if len(end) >0:
            path = path + "&end="+end
    res = create_get_request(path);
    if (res.status_code == 200):
       message = "Measurement found"
    else:
        raise errors.ResourceError(msg=f'Measurements not found')
    logger.debug(message)
    logger.debug(res.content)
    if format == "json":
        return json.loads(res.content.decode('utf-8')), message
    else:
        return res.content, message
#
#create a new measurement in CHORDS
def create_measurement(inst_chords_id, json_body):
    #TODO validate the measurement has all properties requirement and fields are correct
    chords_uri = conf.chords_url+"/measurements/url_create.json?";
    getData = {'email':conf.chords_user_email,
                'api_key': conf.chords_api_key,
                'instrument_id' : inst_chords_id,
                'at': json_body['datetime']
                }
    for itm in json_body['vars']:
        vars = itm #json.loads(itm)
        getData[itm['var_id']]=itm['value']
        # for k in vars:
        #     getData[k]=vars[k]
    logger.debug(chords_uri)
    headers = {
        'Content-Type':'application/x-www-form-urlencoded'
    }
    #CHORDS uses a GET method to create a new measurement
    res = requests.get(chords_uri, data=getData, headers=headers,verify=False)
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

def ping():
    headers = {
        'content-type': "application/json"
    }
    res = requests.get(conf.chords_url,  verify=False)
    return res.status_code
