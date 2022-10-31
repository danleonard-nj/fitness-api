from datetime import datetime
from typing import List

from clients.email_gateway_client import EmailGatewayClient
from clients.fitindex_client import FitIndexClient
from data.fitindex.fitindex_repository import FitIndexRepository
from domain.exceptions import FitIndexRecordException
from domain.feature import FeatureKey
from domain.fitindex import FitIndexMeasurement, MeasurementSummary
from domain.mongo import TimestampRangeFilter
from clients.feature_client import FeatureClientAsync
from framework.concurrency.concurrency import DeferredTasks
from framework.logger.providers import get_logger
from framework.utilities.pinq import first

logger = get_logger(__name__)


class FitIndexService:
    def __init__(
        self,
        fitindex_client: FitIndexClient,
        email_client: EmailGatewayClient,
        fitindex_repository: FitIndexRepository,
        feature_client: FeatureClientAsync
    ):
        self.__fitindex_client = fitindex_client
        self.__email_client = email_client
        self.__fitindex_repository = fitindex_repository
        self.__feature_client = feature_client

    def hello_world(self):
        logger.info('Hello world!')

    async def sync(
        self, days_back=None
    ) -> List[FitIndexMeasurement]:
        '''
        Sync FitIndex data to database by the
        given date range

        `days` : days back to fetch sync data
        '''

        results = await self.__sync_data(
            days_back=int(days_back) or 2)

        email_enabled = await self.__feature_client.is_enabled(
            feature_key=FeatureKey.FitnessSyncEmails)
        logger.info(f'Sync email enabled: {email_enabled}')

        if any(results) and email_enabled:
            logger.info('Sending sync result email')

            sync_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            await self.__email_client.send_datatable_email(
                recipient='dcl525@gmail.com',
                subject=f'FitIndex Sync: {sync_datetime}',
                data=[result.to_dict() for result in results])

        return results

    async def __sync_data(
        self,
        days_back: int
    ) -> List[FitIndexMeasurement]:
        '''
        Sync FitIndex data to database by the given
        date range

        `days_back`: window to pull data to sync
        '''

        logger.info(f'Sync days back: {days_back}')

        # Fetch measurement data from FitIndex client
        data = await self.__fitindex_client.get_measurement_data(
            days_back=days_back)

        results = []
        tasks = DeferredTasks()

        # Short out if there are not records in the
        # given range
        if not any(data):
            logger.info(f'No FitIndex records to sync')
            return results

        for result in data:
            measurement = FitIndexMeasurement(
                data=result)

            # Upsert measurement entity
            tasks.add_task(self.__fitindex_repository.upsert(
                filter=measurement.get_selector(),
                document=measurement.to_dict()))

            results.append(measurement)

        await tasks.run()

        return results

    async def get_measurements(
        self,
        start_date: str,
        end_date: str
    ) -> List[MeasurementSummary]:
        '''
        Get FitIndex measurements by date range

        `start_date`: start date as parsable dateime
        string

        `end_date` : end date as parsable datetime
        string
        '''

        # Parse datetime strings to timestamps and
        # get the range
        timestamp_filter = TimestampRangeFilter(
            start_date=start_date,
            end_date=end_date).get_filter()

        entities = await self.__fitindex_repository.query(
            filter=timestamp_filter)

        # Create domain models
        results = [
            MeasurementSummary(data=entity)
            for entity in entities
        ]

        return results

    async def get_latest_measurement(
        self
    ) -> FitIndexMeasurement:
        '''
        Get the top stored FitIndex record 
        '''

        entities = await self.__fitindex_repository.get_latest()

        if entities is None or not any(entities):
            raise FitIndexRecordException(f'Failed to fetch top record')

        return FitIndexMeasurement(
            data=first(entities))
