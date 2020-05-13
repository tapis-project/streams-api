from flask_migrate import Migrate

from common.utils import TapisApi, handle_error, flask_errors_dict

from service.auth import authn_and_authz
from service.controllers import ProjectsResource, ProjectResource, SitesResource, SiteResource, InstrumentsResource, InstrumentResource, VariablesResource, VariableResource, MeasurementsWriteResource, MeasurementsResource, MeasurementResource, ChannelsResource, ChannelResource, AlertsResource, InfluxResource
from service.models import app

from common.logs import get_logger
logger = get_logger(__name__)
from flask_cors import CORS
CORS(app)
# authentication and authorization ---
@app.before_request
def authnz_for_authenticator():
    authn_and_authz()
    logger.debug("Authorization complete")

# db and migrations ----
#db.init_app(app)
#migrate = Migrate(app, db)

# flask restful API object ----
api = TapisApi(app, errors=flask_errors_dict)

# Set up error handling
api.handle_error = handle_error
api.handle_exception = handle_error
api.handle_user_exception = handle_error

# Add resources
api.add_resource(ProjectsResource, '/v3/streams/projects')
api.add_resource(ProjectResource, '/v3/streams/projects/<project_id>')

api.add_resource(SitesResource, '/v3/streams/projects/<project_id>/sites')
api.add_resource(SiteResource, '/v3/streams/projects/<project_id>/sites/<site_id>')

api.add_resource(InstrumentsResource, '/v3/streams/projects/<project_id>/sites/<site_id>/instruments')
api.add_resource(InstrumentResource, '/v3/streams/projects/<project_id>/sites/<site_id>/instruments/<instrument_id>')

api.add_resource(VariablesResource, '/v3/streams/projects/<project_id>/sites/<site_id>/instruments/<instrument_id>/variables')
api.add_resource(VariableResource, '/v3/streams/projects/<project_id>/sites/<site_id>/instruments/<instrument_id>/variables/<variable_id>')

api.add_resource(MeasurementsWriteResource, '/v3/streams/measurements')
api.add_resource(MeasurementsResource, '/v3/streams/projects/<project_id>/sites/<site_id>/instruments/<instrument_id>/measurements')
api.add_resource(MeasurementResource, '/v3/streams/projects/<project_id>/sites/<site_id>/instruments/<instrument_id>/measurements/<measurement_id>')

api.add_resource(ChannelsResource, '/v3/streams/channels')
api.add_resource(ChannelResource, '/v3/streams/channels/<channel_id>')
api.add_resource(AlertsResource, '/v3/streams/channels/<channel_id>/alerts')

#api.add_resource(StreamsResource, '/v3/streams/projects/<project_id>/channels')
#api.add_resource(StreamResource, '/v3/streams/channels/<channels_id>')

api.add_resource(InfluxResource, '/influx')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
