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

from influxdb_client import InfluxDBClient

from influxdb_client.service.notification_rules_service import NotificationRulesService

from influxdb_client.domain.rule_status_level import RuleStatusLevel

from influxdb_client.domain.status_rule import StatusRule
from influxdb_client.domain.tag_rule import TagRule

from influxdb_client.domain.http_notification_rule import HTTPNotificationRule

from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.domain.check_status_level import CheckStatusLevel
from influxdb_client.domain.dashboard_query import DashboardQuery
from influxdb_client.domain.lesser_threshold import LesserThreshold
from influxdb_client.domain.greater_threshold import GreaterThreshold
from influxdb_client.domain.query_edit_mode import QueryEditMode
from influxdb_client.domain.http_notification_endpoint import HTTPNotificationEndpoint
from influxdb_client.domain.task_status_type import TaskStatusType
from influxdb_client.domain.threshold_check import ThresholdCheck
from influxdb_client.service.checks_service import ChecksService
from influxdb_client.service.notification_endpoints_service import NotificationEndpointsService

url = conf.influxdb_host+':'+conf.influxdb_port
token = conf.influxdb_token
org_name = conf.influxdb_org
bucket_name = conf.influxdb_bucket


def create_check(site_id,inst_id,var_id,check_name,threshold_type, threshold_value):
    logger.debug("Top of create_check")
    with InfluxDBClient(url=url, token=token, org=org_name, debug=False) as client:
        logger.debug('Inside InfluxDBCLienct')
        #uniqueId = str(datetime.datetime.now())

        #Find Organization ID by Organization API.
        org = client.organizations_api().find_organizations(org=org_name)[0]
        
        # Prepare Query

                    #     from(bucket: "streams")
                    # |> range(start: -1s)
                    # |> filter(fn: (r) => r["_measurement"] == "tsdata")
                    # |> filter(fn: (r) => r["_field"] == "value")
                    # |> filter(fn: (r) => r["inst"] == "2")
                    # |> filter(fn: (r) => r["site"] == "2")
                    # |> filter(fn: (r) => r["var"] == "12" and r["_value"] > 90 and r["_value"] < 100)
                    # |> aggregateWindow(every: 1s, fn: mean, createEmpty: false)
                    # |> count(column: "_value")
        query = f'''
                from(bucket:"{bucket_name}") 
                    |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
                    |> filter(fn: (r) => r["_measurement"] == "tsdata")
                    |> filter(fn: (r) => r["_field"] == "value")
                    |> filter(fn: (r) => r["inst"] == "{inst_id}")
                    |> filter(fn: (r) => r["site"] == "{site_id}")
                    |> filter(fn: (r) => r["var"] == "{var_id}")
                    |> aggregateWindow(every: 5s, fn: mean, createEmpty: false)
                '''
        logger.debug(query)
        
        #Create Threshold Check - set status to `Critical` if the count of values matching our expression of > or < our value.
        if threshold_type == ">":
          threshold = GreaterThreshold(value=threshold_value,level=CheckStatusLevel.CRIT)
        else:
          threshold = LesserThreshold(value=threshold_value,level=CheckStatusLevel.CRIT) 

        #Create Check object
        check = ThresholdCheck(name=check_name,
                            status_message_template="For Channel- ${ r._check_name } the threshold alert measurement is: ${ r._source_measurement }",
                            every="5s",
                            offset="2s",
                            query=DashboardQuery(edit_mode=QueryEditMode.ADVANCED, text=query),
                            thresholds=[threshold],
                            org_id=org.id,
                            status=TaskStatusType.ACTIVE)
        logger.debug(check)
        checks_service = ChecksService(api_client=client.api_client)
        check_result = checks_service.create_check(check)
        logger.debug(check_result)
        return check_result

def create_notification_endpoint_actor(endpoint_name, notification_url, actor_id):
    logger.debug("Top of create_noftification_endpoint_actor")
    with InfluxDBClient(url=url, token=token, org=org_name, debug=False) as client:
        logger.debug("In InfluxDBclient")
        #Create HTTP Notification endpoint
        org = client.organizations_api().find_organizations(org=org_name)[0]
        notification_endpoint = HTTPNotificationEndpoint(name=endpoint_name,
                                                        url=notification_url,
                                                        org_id=org.id,
                                                        method='POST',
                                                        auth_method='bearer',token=conf.alert_secret)
        notification_endpoint_service = NotificationEndpointsService(api_client=client.api_client)
        notification_endpoint_result = notification_endpoint_service.create_notification_endpoint(notification_endpoint)
        logger.debug(notification_endpoint_result)
        return notification_endpoint_result

def create_notification_rule(rule_name, notification_endpoint, check_id):
    with InfluxDBClient(url=url, token=token, org=org_name, debug=False) as client:
        """
        Create Notification Rule to notify critical value to HTTP
        """
        org = client.organizations_api().find_organizations(org=org_name)[0]
        notification_rule = HTTPNotificationRule(name=rule_name,
                                                every="5s",
                                                offset="2s",
                                                #message_template="${ r._message }",
                                                status_rules=[StatusRule(current_level=RuleStatusLevel.CRIT)],
                                                tag_rules=[TagRule(key='_check_id',value=check_id)],
                                                endpoint_id=notification_endpoint.id,
                                                org_id=org.id,
                                                status=TaskStatusType.ACTIVE)
        notification_rules_service = NotificationRulesService(api_client=client.api_client)
        notification_rule_result = notification_rules_service.create_notification_rule_with_http_info(notification_rule)
        logger.debug(notification_rule_result)
        return notification_rule_result