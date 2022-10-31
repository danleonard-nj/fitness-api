from datetime import datetime
from typing import Dict, List

from clients.email_gateway_client import EmailGatewayClient
from clients.mfp_client import MyFitnessPalClient
from data.mfp.mfp_repository import MyFitnessPalRepository
from domain.exceptions import MyFitnessPalCredentialException
from domain.feature import FeatureKey
from domain.mfp import (DailySummaryRecord, DiaryRecord, MfpDateUtility,
                        MyFitnessPalSyncResult)
from domain.mongo import TimestampRangeFilter
from clients.feature_client import FeatureClientAsync
from framework.concurrency import DeferredTasks
from framework.logger.providers import get_logger
from framework.serialization.utilities import serialize

logger = get_logger(__name__)


class MfpErrorType:
    AuthError = 'Missing HTTP Header: Authorization'


class MyFitnessPalService:
    def __init__(
        self,
        client: MyFitnessPalClient,
        mfp_repository: MyFitnessPalRepository,
        email_client: EmailGatewayClient,
        feature_client: FeatureClientAsync,
    ):
        self.__client = client
        self.__mfp_repository = mfp_repository
        self.__email_client = email_client
        self.__feature_client = feature_client
        self.__date_util = MfpDateUtility()

        self.__credential_refresh_error = False

    async def sync(
        self,
        days: int
    ):
        logger.info(f'Syncing record days: {days}')
        days_back = int(days) or 1

        date_range = self.__date_util.get_range(
            start=datetime.utcnow(),
            days=days_back)

        logger.info(f'Sync dates: {serialize(date_range)}')

        # Sync days in range concurrently
        tasks = DeferredTasks()
        for date in date_range:
            tasks.add_task(
                coroutine=self.__sync_date_record(
                    date=date))

        records = await tasks.run()

        # Send sync result email
        await self.__send_sync_email(
            records=records)

        return records

    async def __sync_date_record(
        self,
        date=None
    ):
        now = date or datetime.utcnow()
        record_date = self.__date_util.from_date(
            date=now)

        logger.info(f'Sync record date: {record_date}')
        data = await self.__client.get_diary_records(
            date=record_date)

        # Handle sync error, typically due to expired creds
        if 'error' in data:
            logger.info(f'Error occured attempting to fetch MFP record')

            error_description = data.get('error_description')
            logger.info(f'Error description: {error_description}')

            # Check it it's an expired credential causing the error
            if ('error_description' in data
                    and 'Authorization' in error_description):

                # Only trigger the notification on the first error
                if self.__credential_refresh_error is False:
                    logger.info(f'Sending credential refresh notification')

                    self.__credential_refresh_error = True
                    await self.__email_client.send_json_email(
                        subject='MyFitnessPal Credential Refresh Required',
                        recipient='dcl525@gmail.com',
                        data=data)

        if self.__credential_refresh_error:
            raise MyFitnessPalCredentialException(
                f'Credential refresh required')

        # Create domain model for record
        record = DiaryRecord(
            date=record_date,
            data=data)

        await self.__upsert_record(
            record=record)

        return record

    async def __upsert_record(
        self,
        record: DiaryRecord
    ):
        logger.info(f'Upsert record: {record.key}')

        await self.__mfp_repository.upsert(
            filter=record.get_selector(),
            replacement=record.to_dict())

    def __to_sync_results(
        self,
        records
    ) -> List[Dict]:

        models = [
            MyFitnessPalSyncResult(
                data=record.to_dict())
            for record in records
        ]

        return [
            model.to_dict()
            for model in models
        ]

    async def __send_sync_email(
        self,
        records
    ):
        email_enabled = await self.__feature_client.is_enabled(
            feature_key=FeatureKey.FitnessSyncEmails)
        logger.info(f'Sync email enabled: {email_enabled}')

        if email_enabled:
            sync_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            await self.__email_client.send_datatable_email(
                subject=f'MyFitnessPal Sync: {sync_datetime}',
                recipient='dcl525@gmail.com',
                data=self.__to_sync_results(records))

    async def get_daily_summaries(
        self,
        start_date: str,
        end_date: str,
    ):
        logger.info(f'Get daily summaries: {start_date} : {end_date}')

        timestamp_range = TimestampRangeFilter(
            start_date=start_date,
            end_date=end_date).get_filter()

        # Fetch data from database by timestamp range
        data = await self.__mfp_repository.query(
            filter=timestamp_range)

        # Create domain models
        summaries = [
            DailySummaryRecord(
                record=item)
            for item in data
            if 'error' not in item.get(
                'data', dict())
        ]

        return summaries
