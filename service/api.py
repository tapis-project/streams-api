from flask_migrate import Migrate

from common.utils import TapisApi, handle_error, flask_errors_dict

from service.auth import authn_and_authz
from service.controllers import SitesResource, SiteResource, InstrumentsResource, InstrumentResource, VariablesResource, VariableResource, MeasurementsResource, MeasurementResource, StreamsResource, StreamResource
from service.models import app

# authentication and authorization ---
@app.before_request
def authnz_for_authenticator():
    authn_and_authz()

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
api.add_resource(SitesResource, '/sites')
api.add_resource(SiteResource, '/sites/<site_id>')

api.add_resource(InstrumentsResource, '/instruments')
api.add_resource(InstrumentResource, '/instruments/<instrument_id>')

api.add_resource(VariablesResource, '/variables')
api.add_resource(VariableResource, '/variables/<variable_id>')

api.add_resource(MeasurementsResource, '/measurements')
api.add_resource(MeasurementResource, '/measurements/<measurement_id>')

api.add_resource(StreamsResource, '/streams')
api.add_resource(StreamResource, '/streams/<stream_id>')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
