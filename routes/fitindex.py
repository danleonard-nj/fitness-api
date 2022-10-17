from domain.auth import AuthScheme
from framework.rest.blueprints.meta import MetaBlueprint
from quart import request
from services.fitindex.fitindex_service import FitIndexService

fitindex_bp = MetaBlueprint('fitindex_bp', __name__)


@fitindex_bp.configure('/api/fitindex/sync', methods=['POST'], auth_scheme=AuthScheme.Sync)
async def fitindex(container):
    service: FitIndexService = container.resolve(
        FitIndexService)

    days = request.args.get('days')

    data = await service.sync(
        days_back=days)

    return data


@fitindex_bp.configure('/api/fitindex/measurements', methods=['GET'], auth_scheme=AuthScheme.Read)
async def measurements(container):
    service: FitIndexService = container.resolve(
        FitIndexService)

    start = request.args.get('start_date')
    end = request.args.get('end_date')

    data = await service.get_measurements(
        start_date=start,
        end_date=end)

    return data


@fitindex_bp.configure('/api/fitindex/latest', methods=['GET'], auth_scheme=AuthScheme.Read)
async def latest(container):
    service: FitIndexService = container.resolve(
        FitIndexService)

    data = await service.get_latest_measurement()
    return data.to_dict()
