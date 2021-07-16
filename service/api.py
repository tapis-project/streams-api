from flask_migrate import Migrate
from common.utils import TapisApi, handle_error, flask_errors_dict
from service.auth import authn_and_authz
from service.controllers import ProjectsResource, ProjectResource, SitesResource, SiteResource, InstrumentsResource, InstrumentResource, VariablesResource, \
    VariableResource, MeasurementsWriteResource, MeasurementsReadResource, MeasurementsResource, MeasurementResource, ChannelsResource, ChannelResource, AlertsResource, \
    AlertsPostResource, TemplatesResource, TemplateResource, InfluxResource, HelloResource, ReadyResource, HealthcheckResource, MetricsResource, PemsResource, PemsRevokeResource
from service.models import app

# get the logger instance -
from common.logs import get_logger
logger = get_logger(__name__)

# Before every request check the authentication and authorization
@app.before_request
def authnz_for_authenticator():
    authn_and_authz()
    logger.debug("Authentication complete")

# flask restful API object ----
api = TapisApi(app, errors=flask_errors_dict)

# Set up error handling
api.handle_error = handle_error
api.handle_exception = handle_error
api.handle_user_exception = handle_error

# Add resources
## Healthcheck resources
api.add_resource(HelloResource, '/v3/streams/hello')
api.add_resource(ReadyResource, '/v3/streams/ready')
api.add_resource(HealthcheckResource, '/v3/streams/healthcheck')

## Project resources
api.add_resource(ProjectsResource, '/v3/streams/projects')
api.add_resource(ProjectResource, '/v3/streams/projects/<project_id>')

## Sites resources
api.add_resource(SitesResource, '/v3/streams/projects/<project_id>/sites')
api.add_resource(SiteResource, '/v3/streams/projects/<project_id>/sites/<site_id>')

## Instruments resources
api.add_resource(InstrumentsResource, '/v3/streams/projects/<project_id>/sites/<site_id>/instruments')
api.add_resource(InstrumentResource, '/v3/streams/projects/<project_id>/sites/<site_id>/instruments/<instrument_id>')

## Variables resources
api.add_resource(VariablesResource, '/v3/streams/projects/<project_id>/sites/<site_id>/instruments/<instrument_id>/variables')
api.add_resource(VariableResource, '/v3/streams/projects/<project_id>/sites/<site_id>/instruments/<instrument_id>/variables/<variable_id>')

## Measurement resources
api.add_resource(MeasurementsWriteResource, '/v3/streams/measurements')
api.add_resource(MeasurementsReadResource, '/v3/streams/measurements/<instrument_id>')
api.add_resource(MeasurementsResource, '/v3/streams/projects/<project_id>/sites/<site_id>/instruments/<instrument_id>/measurements')
api.add_resource(MeasurementResource, '/v3/streams/projects/<project_id>/sites/<site_id>/instruments/<instrument_id>/measurements/<measurement_id>')

## Channels resources
api.add_resource(ChannelsResource, '/v3/streams/channels')
api.add_resource(ChannelResource, '/v3/streams/channels/<channel_id>')
api.add_resource(AlertsResource, '/v3/streams/channels/<channel_id>/alerts')

## Alerts resources
api.add_resource(AlertsPostResource, '/v3/streams/alerts')
api.add_resource(TemplatesResource, '/v3/streams/templates')
api.add_resource(TemplateResource, '/v3/streams/templates/<template_id>')

## Metrics resources
api.add_resource(MetricsResource, '/v3/streams/metrics')

# Influx resources
api.add_resource(InfluxResource, '/influx')

# Permission resources
api.add_resource(PemsResource, '/v3/streams/roles')
api.add_resource(PemsRevokeResource, '/v3/streams/roles/revokeRole')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
