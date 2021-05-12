import requests
from tapipy.tapis import Tapis
import json
import os
from common.config import conf

def create_streams_service_token():
    t = Tapis(base_url=os.environ['TAPIS_BASEURL'], username=os.environ['STREAMS_USER'], account_type='service',
                 service_password=os.environ['STREAMS_SERVICE_PASSWORD'], tenant_id='master')
    t.get_tokens()


def create_meta_service_token():
    t = Tapis(base_url=os.environ['TAPIS_BASEURL'], username='meta', account_type='service',
                 service_password=os.environ['META_SERVICE_PASSWORD'], tenant_id='master')
    t.get_tokens()

def create_meta_db_grant_pems():
    t = create_meta_service_token()

    pemsString='meta:master:GET,POST,PUT,PATCH,DELETE:'+ os.environ['STREAMS_DB']+':*:*'
    # grant permission to streams/master user to create collections and documents
    t.sk.grantUserPermission(user='streams', tenant='master',
                                 permSpec=pemsString)



## Create the metadata collections with streams/master service token
def create_meta_collections():

    t = create_streams_service_token()

    t.meta.createCollection(db=os.environ['STREAMS_DB'], collection='streams_instrument_index')

    t.meta.createCollection(db=os.environ['STREAMS_DB'], collection='streams_project_metadata')

    t.meta.createCollection(db=os.environ['STREAMS_DB'], collection='streams_alerts_metadata')

    t.meta.createCollection(db=os.environ['STREAMS_DB'], collection='streams_templates_metadata')

    t.meta.createCollection(db=os.environ['STREAMS_DB'], collection='streams_channel_metadata')

    t.meta.createCollection(db=os.environ['STREAMS_DB'], collection='streams_metrics')


if __name__ == "__main__":
    create_meta_db_grant_pems()
    create_meta_collections()
