from typing import Any, Dict, List

from domain.auth import ClientScope
from clients.cache_client import CacheClientAsync
from framework.configuration.configuration import Configuration
from framework.logger.providers import get_logger

from clients.abstractions.gateway_client import GatewayClient
from clients.identity_client import IdentityClient

logger = get_logger(__name__)


class EmailGatewayClient(GatewayClient):
    def __init__(
        self,
        configuration: Configuration,
        identity_client: IdentityClient,
        cache_client: CacheClientAsync
    ):
        super().__init__(
            identity_client=identity_client,
            configuration=configuration,
            cache_client=cache_client,
            cache_key=self.__class__.__name__,
            client_name='kube-tools-api',
            client_scope=ClientScope.EMAIL_GATEWAY_API)

    async def send_email(
        self,
        subject: str,
        recipient: str,
        message: str
    ):
        logger.info(f'Send email: {subject}: {recipient}')

        payload = {
            'recipient': recipient,
            'subject': subject,
            'body': message
        }

        logger.info(f'Payload: {payload}')
        headers = await self.get_headers()

        response = await self.http_client.post(
            url=f'{self.base_url}/api/email/send',
            headers=headers,
            timeout=None,
            json=payload)

        logger.info(f'Status code: {response.status_code}')

        if response.status_code != 200:
            logger.info(f'Failed to send email: {response.text}')

        return response.json()

    async def send_datatable_email(
        self,
        recipient: str,
        subject: str,
        data: List[dict]
    ):
        logger.info(f'Sending datatable email')

        endpoint = f'{self.base_url}/api/email/datatable'
        logger.info(f'Endpoint: {endpoint}')

        content = {
            'recipient': recipient,
            'subject': subject,
            'table': data
        }

        headers = await self.get_headers()
        response = await self.http_client.post(
            url=endpoint,
            json=content,
            timeout=None,
            headers=headers)

        logger.info(f'Response status: {response.status_code}')
        return response.json()

    async def send_json_email(
        self,
        recipient: str,
        subject: str,
        data: Any
    ) -> Dict:
        logger.info(f'Sending JSON email')

        endpoint = f'{self.base_url}/api/email/json'
        logger.info(f'Endpoint: {endpoint}')

        content = {
            'recipient': recipient,
            'subject': subject,
            'json': data
        }

        headers = await self.get_headers()
        response = await self.http_client.post(
            url=endpoint,
            json=content,
            timeout=None,
            headers=headers)

        logger.info(f'Response status: {response.status_code}')
        return response.json()
