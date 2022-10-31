from typing import Any, Tuple

import requests
from framework.clients.http_client import HttpClient
from framework.configuration.configuration import Configuration
from framework.logger.providers import get_logger

logger = get_logger(__name__)


class FeatureClient:
    def __init__(
        self,
        configuration: Configuration
    ):
        self.__enabled = (
            configuration.features.get('enabled') or True
        )

        if self.__enabled:
            self.base_url = configuration.features.get('base_url')
            self.api_key = configuration.features.get('api_key')

    def __get_headers(
        self
    ) -> dict:
        return {
            'api-key': self.api_key
        }

    def get_disabled_feature_response(
        self,
        feature_key: str
    ) -> Tuple[dict, int]:
        '''
        Get a generic response value indicating
        a disabled featre

        `feature_key`: feature flag key
        '''

        return {
            'message': f"Feature '{feature_key}' is not enabled"
        }, 200

    def is_enabled(
        self,
        feature_key: str
    ) -> Any:
        '''
        Get the state of a given feature flag

        `feature_key`: feature flag key
        '''

        if not self.__enabled:
            logger.info(f'Feature evaluation is disabled')
            return True

        logger.info(f'Evaluating feature flag: {feature_key}')
        try:
            response = requests.get(
                url=f'{self.base_url}/api/feature/evaluate/{feature_key}',
                headers=self.__get_headers())

            content = response.json()
            return content.get('value')
        except Exception as ex:
            logger.info(
                f'Failed to fetch feature flag: {feature_key}: {str(ex)}')
            return False


class FeatureClientAsync:
    def __init__(
        self,
        configuration: Configuration
    ):
        self.enabled = (
            configuration.features.get('enabled') or True
        )

        if self.enabled:
            self.base_url = configuration.features.get('base_url')
            self.api_key = configuration.features.get('api_key')

        self.http_client = HttpClient()

    def get_headers(self) -> dict:
        return {
            'api-key': self.api_key
        }

    def get_disabled_feature_response(self, feature_key: str) -> Tuple[dict, int]:
        return {
            'message': f"Feature '{feature_key}' is not enabled"
        }, 200

    async def is_enabled(self, feature_key: str) -> Any:
        if not self.enabled:
            logger.info(f'Feature evaluation is disabled')
            return True

        logger.info(f'Evaluating feature flag: {feature_key}')
        try:
            response = await self.http_client.get(
                url=f'{self.base_url}/api/feature/evaluate/{feature_key}',
                headers=self.get_headers())

            content = response.json()
            return content.get('value')
        except Exception as ex:
            logger.info(
                f'Failed to fetch feature flag: {feature_key}: {str(ex)}')
            return False
