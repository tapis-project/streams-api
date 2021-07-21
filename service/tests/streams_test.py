# A suite of tests for the Tapis Streams.
# Before you start you will need to add the following to the config-local.json file for the tests
# with working username & password for the tenant you are testing against for the other services(sk,meta,abaco etc)
#  "test_tenant_id" : "dev",
#  "test_username" :"testusername",
#  "test_password" :"testpassword"
# Build the tapis/streams-api docker container:  docker build -t tapis/streams-api:latest .
# Build the test docker image: docker build -t tapis/streams-tests -f Dockerfile-tests .
# Run these tests using the built docker image: docker run -it --rm --name=streams-test -p 5000:5000 tapis/streams-tests
#docker build -t tapis/streams-api:latest .; docker build -t tapis/streams-tests -f Dockerfile-tests .;docker run -it --rm --name=streams-test -p 5000:5000 tapis/streams-tests

# Standard library imports...
from unittest.mock import Mock, patch
# Third-party imports...
import pytest
import datetime
import json
from base64 import b64encode
# Local imports...
from service import models
from service import chords
from service import abaco
from service import auth
from service import influx
from service import kapacitor
from service import meta
from service import sk
from service import parse_condition_expr
from service import errors
from service import models
from service.api import app
from common.config import conf
import json
import datetime

time_now= datetime.datetime.today().isoformat()
project_name = 'test_project'+''.join(time_now)
base_url = 'http://localhost:5000/v3/streams/'
projects_url=base_url+'projects/'+project_name
site_name='tapis_demo_site'
site_url = projects_url + '/' + 'sites'
site_details_url= site_url + '/'+ site_name
inst_name='test_instrument'+''.join(time_now)
inst_url = site_url + '/' + site_name+ '/instruments'
inst_details_url = inst_url + '/'+  inst_name
var_name='battery'
var_url = inst_url +'/' + inst_name + '/variables'
var_details_url = var_url +'/'+ var_name
measurements_url = base_url + 'measurements'
measurements_url_list = measurements_url+ '/' + inst_name

@pytest.fixture
def client():
    app.debug = True
    return app.test_client()

def get_token_header():
    from tapipy.tapis import Tapis
    #Create python Tapis client for user
    test_tapis_client = Tapis(base_url= conf.tapis_base_url,
                             username= conf.test_username,
                             password=conf.test_password,
                             account_type='user',
                             tenant_id= conf.test_tenant_id)
    test_tapis_client.get_tokens()
    return {'X-Tapis-Token': test_tapis_client.access_token.access_token}

def test_listing_projects(client):
        with client:
            response = client.get(
                "http://localhost:5000/v3/streams/projects",
                content_type='application/json',
                headers=get_token_header()
            )
            print(f"response.data: {response.data}")
            assert response.status_code == 200


def test_create_projects(client):
    with client:
        payload = {
            "project_name": project_name,
            "project_id":project_name,
            "owner": "testuser2",
            "pi": "testuser2",
            "description": "test project",
            "funding_resource": "tapis",
            "project_url": "test.tacc.utexas.edu",
            "active": True
        }
        response = client.post(
            "http://localhost:5000/v3/streams/projects",
            data=json.dumps(payload),
            content_type='application/json',
            headers=get_token_header()
        )
        print(f"response.data: {response.data}")
        assert response.status_code == 200

def test_update_projects(client):
    with client:
        payload = {
            "project_name": project_name,
            "project_id":project_name,
            "owner": "testuser2",
            "pi": "testuser2",
            "description": "changed description",
            "funding_resource": "tapis",
            "project_url": "test.tacc.utexas.edu",
            "active": True
        }
        response = client.put(
            projects_url,
            data=json.dumps(payload),
            content_type='application/json',
            headers=get_token_header()
        )
        print(f"response.data: {response.data}")
        assert response.status_code == 200

def test_listing_get_project_details(client):
        with client:
            response = client.get(
                projects_url,
                content_type='application/json',
                headers=get_token_header()
            )
            print(f"response.data: {response.data}")
            assert response.status_code == 200


def test_create_site(client):
    with client:
        payload = {
            "project_id": project_name,
            "site_name":site_name,
            "latitude":50,
            "longitude":10,
            "elevation":2,
            "site_id":"tapis_demo_site",
            "description":"test_site"
        }
        response = client.post(
            site_url,
            data=json.dumps(payload),
            content_type='application/json',
            headers=get_token_header()
        )
        print(f"response.data: {response.data}")
        assert response.status_code == 200

def test_update_site(client):
    with client:
        payload = {
            "project_id": project_name,
            "site_name":site_name,
            "latitude":50,
            "longitude":10,
            "elevation":2,
            "site_id":"tapis_demo_site",
            "description":"description changed"
        }
        response = client.put(
            site_details_url,
            data=json.dumps(payload),
            content_type='application/json',
            headers=get_token_header()
        )
        print(f"response.data: {response.data}")
        assert response.status_code == 200


def test_listing_site(client):
        with client:
            response = client.get(
                site_url,
                content_type='application/json',
                headers=get_token_header()
            )
            print(f"response.data: {response.data}")
            assert response.status_code == 200

def test_create_instrument(client):
    with client:
        payload = {
            "project_id": project_name,
            "topic_category_id": "2",
            "site_id": site_name,
            "inst_name": inst_name,
            "inst_description": "demo instrument",
            "inst_id": inst_name
        }
        response = client.post(
            inst_url,
            data=json.dumps(payload),
            content_type='application/json',
            headers=get_token_header()
        )
        print(f"response.data: {response.data}")
        assert response.status_code == 200

def test_update_instrument(client):
    with client:
        payload = {
            "project_id": project_name,
            "topic_category_id": "2",
            "site_id": site_name,
            "inst_name": inst_name,
            "inst_description": "description changed",
            "inst_id": inst_name
        }
        response = client.put(
            inst_details_url,
            data=json.dumps(payload),
            content_type='application/json',
            headers=get_token_header()
        )
        print(f"response.data: {response.data}")
        assert response.status_code == 200

def test_listing_instrument(client):
    with client:
        response = client.get(
            inst_url,
            content_type='application/json',
            headers=get_token_header()
        )
        print(f"response.data: {response.data}")
        assert response.status_code == 200


def test_create_variable(client):
    with client:
        payload = {
            "project_id":project_name,
            "topic_category_id":"2",
            "site_id":site_name,
            "inst_id":inst_name,
            "var_name":var_name,
            "shortname":var_name,
            "var_id":var_name
        }
        response = client.post(
            var_url,
            data=json.dumps(payload),
            content_type='application/json',
            headers=get_token_header()
        )
        print(f"response.data: {response.data}")
        assert response.status_code == 200

def test_list_variables(client):
    with client:
        response = client.get(
            var_url,
            content_type='application/json',
            headers=get_token_header()
        )
        print(f"response.data: {response.data}")
        assert response.status_code == 200


def test_update_variable(client):
    with client:
        payload = {
            "project_id":project_name,
            "topic_category_id":"2",
            "site_id":site_name,
            "inst_id":inst_name,
            "var_name":var_name,
            "shortname":var_name,
            "var_id":var_name
        }
        response = client.put(
            var_details_url,
            data=json.dumps(payload),
            content_type='application/json',
            headers=get_token_header()
        )
        print(f"response.data: {response.data}")
        assert response.status_code == 200


def test_create_measurements(client):
    with client:
        payload = {
            "inst_id":inst_name,
            "vars":[{var_name: 10,
            "datetime":time_now}]
        }
        response = client.post(
            measurements_url,
            data=json.dumps(payload),
            content_type='application/json',
            headers=get_token_header()
        )
        print(f"response.data: {response.data}")
        assert response.status_code == 200

def test_list_measurements(client):
    with client:
        response = client.get(
            measurements_url_list,
            content_type='application/json',
            headers=get_token_header()
        )
        print(f"response.data: {response.data}")
        assert response.status_code == 200
