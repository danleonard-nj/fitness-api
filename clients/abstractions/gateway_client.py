from clients.identity_client import IdentityClient
from framework.clients.cache_client import CacheClientAsync
from framework.clients.http_client import HttpClient
from framework.configuration.configuration import Configuration
from framework.logger.providers import get_logger

logger = get_logger(__name__)


class GatewayClient:
    def __init__(self, container, cache_key: str, client_name: str, client_scope: str):
        self.configuration = container.resolve(Configuration)
        self.__identity_client: IdentityClient = container.resolve(
            IdentityClient)
        self.__cache_client: CacheClientAsync = container.resolve(
            CacheClientAsync)

        self.http_client: HttpClient = HttpClient()

        self.cache_key = cache_key
        self.client_name = client_name
        self.client_scope = client_scope

        self.base_url = self.configuration.gateway.get('base_url')

    async def __get_token(
        self
    ) -> str:
        logger.info('Fetch Azure gateway client token')

        cached_token = await self.__cache_client.get_cache(
            key=f'{self.cache_key}-token')

        if cached_token is not None:
            logger.info('Returning token from cache')
            return cached_token

        logger.info('Fetching token from identity client')
        token = await self.__identity_client.get_token(
            client_name=self.client_name,
            scope=self.client_scope)

        await self.__cache_client.set_cache(
            key=f'{self.cache_key}-token',
            value=token)

        return token

    async def get_headers(self) -> dict:
        token = await self.__get_token()
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
