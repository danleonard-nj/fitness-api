from datetime import datetime, timedelta

import httpx
import pandas as pd
from domain.fitindex import FitIndexConstants
from framework.configuration.configuration import Configuration
from framework.logger.providers import get_logger
from framework.uri.uri import build_url

logger = get_logger(__name__)


class FitIndexClient:
    def __init__(
        self,
        configuration: Configuration
    ):
        self.__base_url = configuration.fitindex.get('base_url')

    async def get_measurement_data(
        self,
        days_back: int
    ) -> pd.DataFrame:
        logger.info(f'Days back: {days_back}')

        lookback = datetime.now() - timedelta(days=int(days_back))
        timestamp = round(lookback.timestamp())

        url = build_url(
            base=self.__base_url,
            user_id=FitIndexConstants.UserId,
            last_at=timestamp,
            app_revision=FitIndexConstants.AppRevision,
            cellphone_type=FitIndexConstants.PhoneType,
            system_type=FitIndexConstants.SystemType,
            zone=FitIndexConstants.Timezone,
            terminal_user_session_key=FitIndexConstants.SessionKey,
            area_code=FitIndexConstants.AreaCode,
            locale=FitIndexConstants.Locale,
            app_id=FitIndexConstants.AppId,
            platform=FitIndexConstants.Platform)

        logger.info(f'Endpoint: {url}')
        async with httpx.AsyncClient(timeout=None) as client:
            response = await client.get(
                url)

            content = response.json()
            return content.get('last_ary')
