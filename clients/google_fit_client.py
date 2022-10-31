import httpx
from clients.identity_client import IdentityClient
from domain.exceptions import (GoogleFitAuthenticationException,
                               GoogleFitRequestFailedException)
from domain.google import GoogleFit
from framework.logger.providers import get_logger
from framework.validators.nulls import none_or_whitespace
from services.google.google_auth_service import GoogleAuthService

logger = get_logger(__name__)


class GoogleFitClient:
    def __init__(
        self,
        auth_service: GoogleAuthService,
        identity_client: IdentityClient
    ):
        self.__auth_service = auth_service
        self.__identity_client = identity_client

        self.__identity_client.get_client(
            client_name='kube-tools-api')

    async def __get_auth_headers(
        self
    ) -> dict:
        logger.info(f'Fetching auth token from Google auth service')

        # Get the named auth client from the Google Auth service
        client = await self.__auth_service.get_client_by_name(
            client_name='kube-tools')

        logger.info(f'Auth client: {client.client_id}: {client.client_name}')

        # Fetch an OAuth token from the auth service (refreshed
        # if necessary)
        creds = await self.__auth_service.get_credentials(
            client_id=client.client_id)

        # Throw on null or empty string for the OAuth
        if none_or_whitespace(creds.token):
            raise GoogleFitAuthenticationException()

        logger.info(f'Token: {creds.token}')
        return {
            'Authorization': f'Bearer {creds.token}'
        }

    async def get_dataset_aggregate(
        self,
        query: dict
    ):
        '''
        Get aggregate data from Google Fit API

        `query`: the dataset query
        '''

        # Get auth headers
        headers = await self.__get_auth_headers()

        async with httpx.AsyncClient(timeout=None) as client:
            response = await client.post(
                url=f'{GoogleFit.BaseUrl}/v1/users/me/dataset:aggregate',
                headers=headers,
                json=query)

            # Throw on failure to fetch
            if response.status_code != 200:
                logger.info(
                    f'Failed to fetch data from Google Fit: {response.json()}')
                raise GoogleFitRequestFailedException(response)

            logger.info(f'Status: {response.status_code}')
            return response.json()
