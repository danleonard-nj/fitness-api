from domain.auth import AuthScheme
from framework.rest.blueprints.meta import MetaBlueprint
from quart import request
from services.mfp.mfp_service import MyFitnessPalService

myfitnesspal_bp = MetaBlueprint('myfitnesspal_bp', __name__)


@myfitnesspal_bp.configure('/api/mfp/diary/sync', methods=['POST'], auth_scheme=AuthScheme.Sync)
async def backfill(container):
    service: MyFitnessPalService = container.resolve(
        MyFitnessPalService)

    days = request.args.get('days')

    return await service.sync(
        days=days)


@myfitnesspal_bp.configure('/api/mfp/diary/daily', methods=['GET'], auth_scheme=AuthScheme.Read)
async def daily_summaries(container):
    service: MyFitnessPalService = container.resolve(
        MyFitnessPalService)

    start = request.args.get('start')
    end = request.args.get('end')

    return await service.get_daily_summaries(
        start_date=start,
        end_date=end)
