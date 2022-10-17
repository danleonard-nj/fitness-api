from framework.rest.blueprints.meta import MetaBlueprint
from quart import request
from domain.auth import AuthScheme
from services.fitness_service import FitnessService

fitness_bp = MetaBlueprint('fitness_bp', __name__)


@fitness_bp.configure('/api/fitness/range', methods=['GET'], auth_scheme=AuthScheme.Read)
async def range(container):
    service: FitnessService = container.resolve(
        FitnessService)

    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    data = await service.get_combined_fitness_data(
        start=start_date,
        end=end_date)

    return data.to_dict()


@fitness_bp.configure('/api/fitness/config', methods=['GET'], auth_scheme=AuthScheme.Read)
async def get_config(container):
    service: FitnessService = container.resolve(
        FitnessService)

    config = await service.get_fitness_config()
    return config.to_dict()


@fitness_bp.configure('/api/fitness/config', methods=['POST'], auth_scheme=AuthScheme.Write)
async def create_config(container):
    service: FitnessService = container.resolve(
        FitnessService)

    body = await request.get_json()
    config = await service.insert_fitness_config(
        data=body)

    return config.to_dict()


@fitness_bp.configure('/api/fitness/calories/delta', methods=['GET'], auth_scheme=AuthScheme.Read)
async def get_deltas(container):
    service: FitnessService = container.resolve(
        FitnessService)

    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    result = await service.get_calorie_deficits(
        start_date=start_date,
        end_date=end_date)

    return result.to_dict()
