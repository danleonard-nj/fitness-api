import json
from datetime import datetime
from typing import List

from data.google.google_auth_repository import GoogleAuthRepository
from domain.google import GoogleAuthClient
from framework.logger.providers import get_logger

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from services.fitindex.fitindex_service import FitIndexService

logger = get_logger(__name__)


class GoogleAuthService:
    def __init__(
        self,
        repository: GoogleAuthRepository
    ):
        self.__repository = repository

    async def get_credentials(
        self,
        client_id,
        scopes=None
    ) -> Credentials:
        logger.info(f'Get credentials for client: {client_id}')

        entity = await self.__repository.get({
            'client_id': client_id
        })

        if entity is None:
            raise Exception(f"No client with the ID '{client_id}' exists")

        client = GoogleAuthClient(
            data=entity)

        logger.info(f'Auth client fetched: {client.client_id}')
        creds = client.get_google_creds(
            scopes=scopes)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info(f'Refreshing credentials')
                creds.refresh(Request())

                logger.info(f'Credentials refreshed successfully')
                client.credentials = json.loads(creds.to_json())
                client.last_refresh = datetime.now().isoformat()

                logger.info(f'Saving refreshed credentials')
                await self.update_client(
                    client=client)

        logger.info(f'Credentials fetched successfully')
        return creds

    async def create_client(
        self,
        data
    ) -> GoogleAuthClient:
        logger.info(f'Creating auth client')

        client = GoogleAuthClient(
            data=data)
        client.new_client()

        logger.info(f'Auth client ID: {client.client_id}')
        await self.__repository.insert(
            document=client.to_dict())

        return client

    async def get_clients(
        self
    ) -> List[GoogleAuthClient]:
        logger.info(f'Fetching stored clients')
        entities = await self.__repository.get_all()

        clients = [
            GoogleAuthClient(data=entity)
            for entity in entities]

        return clients

    async def get_client(
        self,
        client_id: str
    ) -> GoogleAuthClient:
        logger.info(f'Fetching stored client: {client_id}')
        entity = await self.__repository.get({
            'client_id': client_id
        })

        client = GoogleAuthClient(
            data=entity)

        return client

    async def get_client_by_name(
        self,
        client_name: str
    ) -> GoogleAuthClient:
        logger.info(f'Fetching stored client: {client_name}')
        entity = await self.__repository.get({
            'client_name': client_name
        })

        client = GoogleAuthClient(
            data=entity)

        return client

    async def refresh_client(
        self,
        client: GoogleAuthClient
    ):
        logger.info(f'Refreshing client: {client.client_name}')

        try:
            creds = client.get_google_creds()
            creds.refresh(Request())

            client.credentials = json.loads(creds.to_json())
            client.last_refresh = datetime.now().isoformat()

            logger.info(f'Client refreshed successfully')
        except Exception as ex:
            logger.info(
                f'Failed to refresh token for client: {client.client_name}: {str(ex)}')
            client.error = str(ex)

        await self.update_client(
            client=client)

    async def refresh_clients(
        self
    ):
        clients = await self.get_clients()

        for client in clients:
            await self.refresh_client(
                client=client)

        return clients

    async def update_client(
        self,
        client: GoogleAuthClient
    ):
        logger.info(f'Updaing auth client: {client.client_name}')

        selector = client.get_selector()
        entity = await self.__repository.get(selector)

        if entity is None:
            raise Exception(
                f"No client with the name '{client.client_name}' exists")

        await self.__repository.replace(
            selector=selector,
            document=client.to_dict())
