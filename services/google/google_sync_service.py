from datetime import datetime, timedelta
from typing import List, Tuple

from domain.google import GoogleFitCombinedData, GoogleFitDataPoint, GoogleFitRequest
from framework.concurrency import DeferredTasks
from framework.logger import get_logger
from services.google.google_fit_service import GoogleFitService

logger = get_logger(__name__)


class GoogleFitSyncService:
    def __init__(self, container):
        self.__google_fit_service: GoogleFitService = container.resolve(
            GoogleFitService)

    def __get_sync_range(
        self,
        days_back=7
    ) -> Tuple[str, str]:
        '''
        Calculate and return dates for the sync
        range as ISO datetime strings

        `days_back`: days from now to look back
        for data pull
        '''

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(
            days=days_back or 7)

        return (
            start_date.isoformat(),
            end_date.isoformat()
        )

    async def __get_sync_data(
        self,
        start_date: str,
        end_date: str
    ) -> Tuple[List[GoogleFitDataPoint], List[GoogleFitDataPoint], List[GoogleFitDataPoint]]:
        '''
        Get Google Fit data for a given range
        to sync

        `start_date`: start date as parsable date 
        string

        `end_date`: end date as parsable date string
        '''

        # Build request for Google Fit client
        request = GoogleFitRequest(
            start_date=start_date,
            end_date=end_date)

        logger.info(f'Fetching data from Fit service')

        # Query Google Fit for steps, minutes and calories
        # concurrently
        tasks = DeferredTasks(
            self.__google_fit_service.get_steps(req=request),
            self.__google_fit_service.get_active_minutes(req=request),
            self.__google_fit_service.get_calories_expended(req=request))

        return await tasks.run()

    async def sync(
        self,
        days_back: int
    ) -> GoogleFitCombinedData:

        start_date, end_date = self.__get_sync_range(
            days_back=days_back)

        logger.info(f'Fit sync start: {start_date}')
        logger.info(f'Fit sync end: {end_date}')

        # Get Google Fit data for sync date range
        steps, minutes, calories = await self.__get_sync_data(
            start_date=start_date,
            end_date=end_date)

        logger.info(f'Upserting sync records')

        # Run the db upsert tasks concurrently
        upserts = DeferredTasks(
            self.__google_fit_service.upsert_steps(
                steps=steps,
                get_selector=lambda record: {
                    'key': record.key
                }),
            self.__google_fit_service.upsert_minutes(
                minutes=minutes,
                get_selector=lambda record: {
                    'key': record.key
                }),
            self.__google_fit_service.upsert_calories(
                calories=calories,
                get_selector=lambda record: {
                    'key': record.key
                }))

        await upserts.run()

        # TODO: Model for this return

        return GoogleFitCombinedData(
            minutes=minutes,
            calories=calories,
            steps=steps)
