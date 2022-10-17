from domain.auth import AuthScheme
from domain.google import GoogleFitRequest
from framework.rest.blueprints.meta import MetaBlueprint
from quart import request
from services.google.google_fit_service import GoogleFitService
from services.google.google_sync_service import GoogleFitSyncService

google_fit_bp = MetaBlueprint('google_fit_bp', __name__)


@google_fit_bp.configure('/api/google/fit/steps', methods=['GET'], auth_scheme=AuthScheme.Read)
async def fit_steps(container):
    service: GoogleFitService = container.resolve(
        GoogleFitService)

    steps_request = GoogleFitRequest(
        start_date=request.args.get('start'),
        end_date=request.args.get('end'))

    return await service.get_steps(
        req=steps_request)


@google_fit_bp.configure('/api/google/fit/calories', methods=['GET'], auth_scheme=AuthScheme.Read)
async def fit_calories(container):
    service: GoogleFitService = container.resolve(
        GoogleFitService)

    fit_request = GoogleFitRequest(
        start_date=request.args.get('start'),
        end_date=request.args.get('end'))

    return await service.get_calories_expended(
        req=fit_request)


@google_fit_bp.configure('/api/google/fit/activity', methods=['GET'], auth_scheme=AuthScheme.Read)
async def fit_activity(container):
    service: GoogleFitService = container.resolve(
        GoogleFitService)

    fit_request = GoogleFitRequest(
        start_date=request.args.get('start'),
        end_date=request.args.get('end'))

    return await service.get_active_minutes(
        req=fit_request)


@google_fit_bp.configure('/api/google/fit/sync', methods=['POST'], auth_scheme=AuthScheme.Sync)
async def fit_sync(container):
    service: GoogleFitSyncService = container.resolve(
        GoogleFitSyncService)

    days_back = int(request.args.get('days'))

    result = await service.sync(
        days_back=days_back)

    return result.to_dict()


@google_fit_bp.configure('/api/google/fit/combined', methods=['GET'], auth_scheme=AuthScheme.Read)
async def fit_query(container):
    service: GoogleFitService = container.resolve(
        GoogleFitService)

    start = request.args.get('start_date')
    end = request.args.get('end_date')

    return await service.get_combined_fitness_data(
        start_date=start,
        end_date=end)
