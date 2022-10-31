from framework.configuration.configuration import Configuration
from framework.logger.providers import get_logger
from framework.clients.http_client import HttpClient
from framework.validators.nulls import not_none
from framework.serialization.utilities import serialize
from framework.auth.configuration import AzureAdConfiguration
from framework.constants.constants import ConfigurationKey

logger = get_logger(__name__)


class IdentityClient:
    def __init__(
        self,
        configuration: Configuration
    ):
        not_none(configuration, 'configuration')

        self.ad_auth: AzureAdConfiguration = configuration.ad_auth
        self.http_client = HttpClient()

        logger.info('Configuring identity client')
        self.clients = {}

        logger.info('Loading identity clients from configuration')
        for client in self.ad_auth.clients:
            self.add_client(client)

    def add_client(self, config: dict) -> None:
        self.clients.update({
            config.get('name'): {
                'client_id': config.get(
                    ConfigurationKey.CLIENT_CLIENT_ID),
                'client_secret': config.get(
                    ConfigurationKey.CLIENT_CLIENT_SECRET),
                'grant_type': config.get(
                    ConfigurationKey.CLIENT_GRANT_TYPE),
                'scope': ' '.join(
                    config.get(ConfigurationKey.CLIENT_SCOPE))
            }
        })

    async def get_token(self, client_name: str, scope: str = None):
        client = self.clients.get(client_name)
        if client is None:
            raise Exception(f'No client exists with the name {client_name}')

        if scope is not None:
            client['scope'] = scope

        try:
            logger.info(f'Client: {serialize(client)}')

            response = await self.http_client.post(
                url=f'{self.ad_auth.identity_url}',
                data=client,
                headers={'ContentType': 'application/json'})

            if response.status_code == 200:
                logger.info(f'Response: {response.text}')
                token = response.json().get('access_token')
                logger.info(f'Token: {token}')

                return token
            else:
                raise Exception(
                    f'Failed to fetch token from identity server: {response.status_code}: {response.text}')
        except Exception as ex:
            raise Exception(str(ex))

    def get_client(self, client_name):
        if not self.clients.get(client_name):
            raise Exception(f'No client with the name {client_name} exists')

        return self.clients.get(client_name)
