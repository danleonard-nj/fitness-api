from framework.abstractions.abstract_request import RequestContextProvider
from framework.logger.providers import get_logger
from framework.serialization.serializer import configure_serializer
from framework.swagger.quart.swagger import Swagger
from framework.utilities.object_utils import getattr_or_none
from quart import Quart

from routes.fitindex import fitindex_bp
from routes.fitness import fitness_bp
from routes.google_auth import google_auth_bp
from routes.google_fit import google_fit_bp
from routes.mfp import myfitnesspal_bp
from routes.health import health_bp
from utilities.provider import ContainerProvider

logger = get_logger(__name__)
app = Quart(__name__)


configure_serializer(app)


app.register_blueprint(fitindex_bp)
app.register_blueprint(myfitnesspal_bp)
app.register_blueprint(google_fit_bp)
app.register_blueprint(fitness_bp)
app.register_blueprint(google_auth_bp)
app.register_blueprint(health_bp)

ContainerProvider.initialize_provider()


@app.before_serving
async def startup():
    RequestContextProvider.initialize_provider(
        app=app)


@app.errorhandler(Exception)
def error_handler(e):
    app.logger.exception('Failed')
    message = {'error': str(e)}
    return message, getattr_or_none(
        obj=e,
        name='code') or 500


swag = Swagger(app=app, title='kube-tools-api')
swag.configure()

if __name__ == '__main__':
    app.run(debug=True, port='5089')
