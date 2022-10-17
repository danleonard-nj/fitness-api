import json
from math import fabs
import os
from datetime import datetime
from typing import Union

import httpx
import requests
from domain.exceptions import MyFitnessPalCredentialException
from domain.mfp import MyFitnessPal
from framework.logger.providers import get_logger
from framework.uri import build_url
from requests.cookies import RequestsCookieJar

logger = get_logger(__name__)


class MyFitnessPalClient:
    def __init__(self, container):
        self.base_url = MyFitnessPal.BaseUrl
        self.cookies = self.get_credentials()

    def get_credentials(
        self
    ) -> RequestsCookieJar:

        # Verify credential file exists
        # TODO: Fetch creds from database
        if not os.path.exists(MyFitnessPal.CredentialFile):
            raise MyFitnessPalCredentialException(
                'No stored credentals exist')

        logger.info(f'Loading stored credentials')
        with open(MyFitnessPal.CredentialFile, 'r') as file:
            data = json.loads(file.read())

        # Create cookie jar from stored credentials
        session = requests.session()
        for cookie in data:
            session.cookies.set(
                name=cookie.get('name'),
                value=cookie.get('value'))

        return session.cookies

    async def get_diary_records(
        self,
        date: Union[str, datetime] = None
    ) -> dict:
        cookies = self.get_credentials()

        async with httpx.AsyncClient(cookies=cookies, timeout=None) as client:
            url = build_url(
                base=f'{self.base_url}/api/services/diary',
                entry_date=date,
                fields='all',
                verify=False,
                types='food_entry')

            logger.info(f'MyFitnessPal Endpoint: {url}')

            response = await client.get(
                url=url)
            return response.json()
