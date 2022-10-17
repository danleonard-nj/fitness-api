from quart import Blueprint

health_bp = Blueprint('health_bp', __name__)


@health_bp.route('/api/health/alive')
def alive():
    return {'status': 'ok'}, 200


@health_bp.route('/api/health/ready')
def ready():
    return {'status': 'ok'}, 200
