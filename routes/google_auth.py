from domain.auth import AuthScheme
from domain.google import GoogleTokenResponse
from framework.rest.blueprints.meta import MetaBlueprint
from quart import request
from services.google.google_auth_service import GoogleAuthService

google_auth_bp = MetaBlueprint('google_auth_bp', __name__)


@google_auth_bp.configure('/api/google/client', methods=['GET'], auth_scheme=AuthScheme.Read)
async def get_clients(container):
    service: GoogleAuthService = container.resolve(
        GoogleAuthService)

    clients = await service.get_clients()

    return {
        'clients': clients
    }


@google_auth_bp.configure('/api/google/client', methods=['POST'], auth_scheme=AuthScheme.Write)
async def create_client(container):
    service: GoogleAuthService = container.resolve(
        GoogleAuthService)

    data = await request.get_json()

    client = await service.create_client(
        data=data)

    return client
