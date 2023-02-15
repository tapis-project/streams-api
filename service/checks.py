from influxdb_client.domain.slack_notification_endpoint import SlackNotificationEndpoint
from influxdb_client.domain.slack_notification_rule import SlackNotificationRule
from influxdb_client.service.notification_endpoints_service import NotificationEndpointsService
from influxdb_client.service.checks_service import ChecksService
from influxdb_client.domain.deadman_check import DeadmanCheck
from influxdb_client.domain.threshold_check import ThresholdCheck
from influxdb_client.domain.task_status_type import TaskStatusType
from influxdb_client.domain.http_notification_endpoint import HTTPNotificationEndpoint
from influxdb_client.domain.query_edit_mode import QueryEditMode
from influxdb_client.domain.greater_threshold import GreaterThreshold
from influxdb_client.domain.lesser_threshold import LesserThreshold
from influxdb_client.domain.dashboard_query import DashboardQuery
from influxdb_client.domain.check_status_level import CheckStatusLevel
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.domain.http_notification_rule import HTTPNotificationRule
from influxdb_client.domain.tag_rule import TagRule
from influxdb_client.domain.status_rule import StatusRule
from influxdb_client.domain.rule_status_level import RuleStatusLevel
from influxdb_client.service.notification_rules_service import NotificationRulesService
from influxdb_client import InfluxDBClient
from tapisservice.logs import get_logger
from tapisservice import errors
import datetime
import enum
import requests
import json
import re
from flask import g, Flask
from tapisservice.config import conf
app = Flask(__name__)

# get the logger instance -
logger = get_logger(__name__)


url = conf.influxdb_host+':'+conf.influxdb_port
token = conf.influxdb_token
org_name = conf.influxdb_org
#bucket_name = conf.influxdb_bucket

# replace references to a bucket with streams so it cannot be hardcoded


def clean_template_script(template_script):
    import re
    t_script = re.sub(
        r'from\(bucket:[^;\)]*', '''from(bucket:"{bucket_name}"''', template_script)
    t_script2 = re.sub(
        r'from\("bucket":[^;\)]*', '''from(bucket:"{bucket_name}"''', t_script)
    t_script3 = re.sub(
        r"from\('bucket':[^;\)]*", '''from(bucket:"{bucket_name}"''', t_script2)
    return t_script3


def create_check(template, site_id, inst_id, var_id, check_name, threshold_type, threshold_value, check_message, bucket_name):
    logger.debug("Top of create_check")
    with InfluxDBClient(url=url, token=token, org=org_name) as client:
        logger.debug('Inside InfluxDBCLienct')
        #uniqueId = str(datetime.datetime.now())

        # Find Organization ID by Organization API.
        org = client.organizations_api().find_organizations(org=org_name)[0]

        # Prepare Query
        scriptvars = {}
        scriptvars["var_id"] = var_id
        scriptvars["site_id"] = site_id
        scriptvars["inst_id"] = inst_id
        scriptvars["bucket_name"] = bucket_name
        logger.debug(template)
        template["script"] = clean_template_script(template["script"])
        logger.debug(template['script'])
        # replace the template script variable placeholders with actual values
        query = template["script"].format(**scriptvars)
        logger.debug(query)

        # Create Threshold Check - set status to `Critical` if the count of values matching our expression of > or < our value.
        if threshold_type == ">":
            threshold = GreaterThreshold(
                value=threshold_value, level=CheckStatusLevel.CRIT)
        else:
            threshold = LesserThreshold(
                value=threshold_value, level=CheckStatusLevel.CRIT)

        # Create Check object
        msg_template = '{"trigger_info":"For Channel- ${ r._check_name } the threshold alert triggered at ${r._time} value=${ r.value }.","value:"${ r.value }"}'
        if check_message != '':
            msg_template = check_message

        check = ThresholdCheck(name=check_name,
                            status_message_template=msg_template,
                            every="5s",
                            offset="2s",
                            query=DashboardQuery(edit_mode=QueryEditMode.ADVANCED, text=query),
                            thresholds=[threshold],
                            org_id=org.id,
                            status=TaskStatusType.ACTIVE)

        logger.debug(check)
        try:
            checks_service = ChecksService(api_client=client.api_client)
            check_result = checks_service.create_check(check)
            logger.debug(check_result)
            return check_result, "success"
        except Exception as e:
            logger.debug(e)
            return e, "error"


def create_deadmancheck(template, site_id, inst_id, var_id, check_name, time_since, check_message, bucket_name, report_zero=False, stale_time=None, every=None, offset=None):
    logger.debug("Top of create_check")
    with InfluxDBClient(url=url, token=token, org=org_name) as client:
        logger.debug('Inside InfluxDBCLienct')
        #uniqueId = str(datetime.datetime.now())

        # Doing error checking on parameters
        regex = re.compile("(\\d*)(ns|us|ms|s|m|h|d|w|mo|y)$")

        if not regex.match(time_since):
            msg = f"Incorrect time_since format: {time_since} should be in the form of \"(\\d*)(ns|us|ms|s|m|h|d|w|mo|y)$\""
            logger.debug(msg)
            return errors.ResourceError(msg=msg), "error"

        if stale_time is not None and not regex.match(stale_time):
            msg = f"Incorrect stale_time format: {stale_time} should be in the form of \"(\\d*)(ns|us|ms|s|m|h|d|w|mo|y)$\""
            logger.debug(msg)
            return errors.ResourceError(msg=msg), "error"

        if every is not None and not regex.match(every):
            msg = f"Incorrect every format: {every} should be in the form of \"(\\d*)(ns|us|ms|s|m|h|d|w|mo|y)$\""
            logger.debug(msg)
            return errors.ResourceError(msg=msg), "error"

        if offset is not None and not regex.match(offset):
            msg = f"Incorrect offset format: {offset} should be in the form of \"(\\d*)(ns|us|ms|s|m|h|d|w|mo|y)$\""
            logger.debug(msg)
            return errors.ResourceError(msg=msg), "error"



        # Find Organization ID by Organization API.
        org = client.organizations_api().find_organizations(org=org_name)[0]

        # Prepare Query
        scriptvars = {}
        scriptvars["var_id"] = var_id
        scriptvars["site_id"] = site_id
        scriptvars["inst_id"] = inst_id
        scriptvars["bucket_name"] = bucket_name
        logger.debug(template)
        template["script"] = clean_template_script(template["script"])
        logger.debug(template['script'])
        # replace the template script variable placeholders with actual values
        query = template["script"].format(**scriptvars)
        logger.debug(query)

        # Create Check object
        msg_template = '{"trigger_info":"For Channel- ${ r._check_name } the threshold alert triggered at ${r._time} value=${ r.value }.","value:"${ r.value }"}'
        if check_message != '':
            msg_template = check_message

        # Checks if every was given, otherwise defaults to be same as time_since
        if every is None:
            every = time_since

        # Default offset
        if offset is None:
            offset = "15s"

        # Calculate stale_time to send a max of 20 notifs
        if stale_time is None:
            regex = re.compile("(\\d*)(ns|ms|us|mo)$")
            result = regex.match(time_since)
            if result:
                time_unit = result.group(2)
                time = int(result.group(1))
            else:
                time_unit = every[-1]
                time = int(every[0:-1])

            time *= 20
            stale_time = str(time) + time_unit

        check = DeadmanCheck(name=check_name,
                             status_message_template=msg_template,
                             every=every,
                             offset=offset,
                             query=DashboardQuery(
                                 edit_mode=QueryEditMode.ADVANCED, text=query),
                             time_since=time_since,
                             stale_time=stale_time,
                             report_zero=report_zero,
                             level=CheckStatusLevel.CRIT,
                             org_id=org.id,
                             status=TaskStatusType.ACTIVE)
        logger.debug(check)
        try:
            checks_service = ChecksService(api_client=client.api_client)
            check_result = checks_service.create_check(check)
            logger.debug(check_result)
            return check_result, "success"
        except Exception as e:
            logger.debug(e)
            return e, "error"


def create_notification_endpoint_http(endpoint_name, notification_url):
    logger.debug("Top of create_noftification_endpoint_http")
    with InfluxDBClient(url=url, token=token, org=org_name) as client:
        logger.debug("In InfluxDBclient")
        # Create HTTP Notification endpoint
        org = client.organizations_api().find_organizations(org=org_name)[0]
        notification_endpoint = HTTPNotificationEndpoint(name=endpoint_name,
                                                         url=notification_url,
                                                         org_id=org.id,
                                                         method='POST',
                                                         auth_method='bearer', token=conf.alert_secret)
        try:
            notification_endpoint_service = NotificationEndpointsService(
                api_client=client.api_client)
            notification_endpoint_result = notification_endpoint_service.create_notification_endpoint(
                notification_endpoint)
            logger.debug(notification_endpoint_result)
            return notification_endpoint_result, "success"
        except Exception as e:
            logger.debug(e)
            return e, "error"


def create_http_notification_rule(rule_name, notification_endpoint, check_id):
    logger.debug("Top of  create_http_notification_rule")
    with InfluxDBClient(url=url, token=token, org=org_name, debug=False) as client:
        logger.debug("In InfluxDBclient")
        org = client.organizations_api().find_organizations(org=org_name)[0]
        notification_rule = HTTPNotificationRule(name=rule_name,
                                                 every="5s",
                                                 offset="2s",
                                                 #message_template="${ r._message }",
                                                 status_rules=[StatusRule(
                                                     current_level=RuleStatusLevel.CRIT)],
                                                 tag_rules=[
                                                     TagRule(key='_check_id', value=check_id)],
                                                 endpoint_id=notification_endpoint.id,
                                                 org_id=org.id,
                                                 status=TaskStatusType.ACTIVE)
        logger.debug("Notification Rule obj: " + str(notification_rule))
        try:
            notification_rules_service = NotificationRulesService(
                api_client=client.api_client)
            notification_rule_result = notification_rules_service.create_notification_rule_with_http_info(
                notification_rule)
            logger.debug(notification_rule_result[0])
            return notification_rule_result, "success"
        except Exception as e:
            logger.debug(e)
            return e, "error"


def create_slack_notification_endpoint(endpoint_name, notification_url):
    logger.debug("Top of  create_slack_notification_endpoint")
    with InfluxDBClient(url=url, token=token, org=org_name) as client:
        logger.debug("In InfluxDBclient")
        org = client.organizations_api().find_organizations(org=org_name)[0]

        notification_endpoint = SlackNotificationEndpoint(name=endpoint_name,
                                                          url=notification_url,
                                                          org_id=org.id)
        try:
            notification_rules_service = NotificationRulesService(
                api_client=client.api_client)
            notification_rule_result = notification_rules_service.create_notification_rule(
                notification_endpoint)
            logger.debug(notification_rule_result)
            return notification_rule_result, "success"
        except Exception as e:
            logger.debug(e)
            return e, "error"


def create_slack_notification_rule(rule_name, notification_endpoint, check_id):
    logger.debug("Top of  create_slack_notification_rule")
    with InfluxDBClient(url=url, token=token, org=org_name) as client:
        logger.debug("In InfluxDBclient")
        org = client.organizations_api().find_organizations(org=org_name)[0]
        notification_rule = SlackNotificationRule(name=rule_name,
                                                  every="10s",
                                                  offset="0s",
                                                  message_template="${ r._message }",
                                                  status_rules=[StatusRule(
                                                      current_level=RuleStatusLevel.CRIT)],
                                                  tag_rules=[
                                                      TagRule(key='_check_id', value=check_id)],
                                                  endpoint_id=notification_endpoint.id,
                                                  org_id=org.id,
                                                  status=TaskStatusType.ACTIVE)
        try:
            notification_rules_service = NotificationRulesService(
                api_client=client.api_client)
            notification_rule_result = notification_rules_service.create_notification_rule(
                notification_rule)
            logger.debug(notification_rule_result)
            return notification_rule_result, "sucess"
        except Exception as e:
            logger.debug(e)
            return e, "error"


def delete_check(channel):
    logger.debug("Top of delete_check")
    with InfluxDBClient(url=url, token=token, org=org_name, debug=False) as client:

        try:
            notification_endpoint_service = NotificationEndpointsService(
                api_client=client.api_client)
            notification_endpoint_service.delete_notification_endpoints_id(
                endpoint_id=channel["endpoint_id"])
        except Exception as e:
            logger.debug(e)
        try:
            notification_rules_service = NotificationRulesService(
                api_client=client.api_client)
            notification_rules_service.delete_notification_rules_id(
                rule_id=channel["notification_rule_id"])
        except Exception as e:
            logger.debug(e)
        try:
            checks_service = ChecksService(api_client=client.api_client)
            check_result = checks_service.delete_checks_id(
                check_id=channel["check_id"])
        except Exception as e:
            logger.debug(e)

        return True
