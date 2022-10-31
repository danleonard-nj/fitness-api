from unittest.mock import MagicMock
import uuid
from clients.email_gateway_client import EmailGatewayClient
from clients.fitindex_client import FitIndexClient
from clients.google_fit_client import GoogleFitClient
from clients.identity_client import IdentityClient
from clients.mfp_client import MyFitnessPalClient
from data.fitindex.fitindex_repository import FitIndexRepository
from data.fitness_repository import FitnessConfigRepository
from data.google.active_minutes_repository import GoogleFitMinutesRepository
from data.google.calories_repository import GoogleFitCaloriesRepository
from data.google.google_auth_repository import GoogleAuthRepository
from data.google.steps_repositories import GoogleFitStepsRepository
from data.mfp.mfp_repository import MyFitnessPalRepository
from domain.auth import AdRole, AuthScheme
from framework.abstractions.abstract_request import RequestContextProvider
from framework.auth.azure import AzureAd
from framework.auth.configuration import AzureAdConfiguration
from framework.configuration.configuration import Configuration
from quart import Quart
from services.fitindex.fitindex_service import FitIndexService
from services.fitness_service import FitnessService
from services.google.google_auth_service import GoogleAuthService
from services.google.google_fit_service import GoogleFitService
from services.google.google_sync_service import GoogleFitSyncService
from services.mfp.mfp_service import MyFitnessPalService
from clients.cache_client import CacheClientAsync
from clients.feature_client import FeatureClientAsync
from framework.logger import get_logger

from framework.di.static_provider import ProviderBase
from framework.di.service_collection import ServiceCollection


from motor.motor_asyncio import AsyncIOMotorClient

logger = get_logger(__name__)


def configure_azure_ad(container):
    configuration = container.resolve(Configuration)

    # Hook the Azure AD auth config into the service
    # configuration
    ad_auth: AzureAdConfiguration = configuration.ad_auth
    azure_ad = AzureAd(
        tenant=ad_auth.tenant_id,
        audiences=ad_auth.audiences,
        issuer=ad_auth.issuer)

    azure_ad.add_authorization_policy(
        name='default',
        func=lambda t: True)

    azure_ad.add_authorization_policy(
        name=AuthScheme.Read,
        func=lambda t: AdRole.Read in t.get('roles', []))

    azure_ad.add_authorization_policy(
        name=AuthScheme.Write,
        func=lambda t: AdRole.Write in t.get('roles', []))

    azure_ad.add_authorization_policy(
        name=AuthScheme.Sync,
        func=lambda t: AdRole.Sync in t.get('roles', []))

    return azure_ad


def get_client(provider):
    configuration = provider.resolve(Configuration)
    connection_string = configuration.mongo.get('connection_string')

    logger.info(f'Built client')
    client = AsyncIOMotorClient(connection_string)
    client.id = str(uuid.uuid4())
    logger.info(f'Client ID: {client.id}')
    return client


class ContainerProvider(ProviderBase):
    @classmethod
    def configure_container(cls):
        container = ServiceCollection()
        container.add_singleton(Configuration)

        container.add_singleton(
            dependency_type=AzureAd,
            factory=configure_azure_ad)

        container.add_singleton(
            dependency_type=AsyncIOMotorClient,
            factory=get_client)

        # Framework
        container.add_singleton(CacheClientAsync)
        container.add_singleton(FitnessConfigRepository)
        container.add_singleton(FeatureClientAsync)

        # Clients
        container.add_singleton(EmailGatewayClient)
        container.add_singleton(FitIndexClient)
        container.add_transient(GoogleFitClient)
        container.add_singleton(IdentityClient)
        container.add_singleton(MyFitnessPalClient)

        # Repositories
        container.add_singleton(GoogleFitStepsRepository)
        container.add_singleton(GoogleFitCaloriesRepository)
        container.add_singleton(GoogleFitMinutesRepository)
        container.add_singleton(FitIndexRepository)
        container.add_singleton(GoogleAuthRepository)
        container.add_singleton(MyFitnessPalRepository)

        # Services
        container.add_transient(GoogleAuthService)
        container.add_transient(GoogleFitService)
        container.add_transient(FitIndexService)
        container.add_transient(FitnessService)
        container.add_transient(MyFitnessPalService)
        container.add_transient(GoogleFitSyncService)

        return container


def add_container_hook(app: Quart):
    def inject_container():
        RequestContextProvider.initialize_provider(
            app=app)

    app.before_request_funcs.setdefault(
        None, []).append(
            inject_container)
