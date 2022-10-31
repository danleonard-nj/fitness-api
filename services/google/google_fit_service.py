from datetime import datetime, timedelta
from typing import Callable, Dict, List

import pandas as pd
from clients.google_fit_client import GoogleFitClient
from data.google.active_minutes_repository import GoogleFitMinutesRepository
from data.google.calories_repository import GoogleFitCaloriesRepository
from data.google.steps_repositories import GoogleFitStepsRepository
from domain.google import (FitAggregateDataset, GoogleFitDataPoint,
                           GoogleFitDataSource, GoogleFitDataType,
                           GoogleFitRequest, GoogleFitValueType)
from domain.mongo import TimestampRangeFilter
from clients.feature_client import FeatureClientAsync
from framework.concurrency import DeferredTasks
from framework.logger.providers import get_logger

logger = get_logger(__name__)


def where(items, func):
    results = []
    for item in items:
        if func(item) is True:
            results.append(item)
    return results


class GoogleFitService:
    def __init__(
        self,
        client: GoogleFitClient,
        steps_repository: GoogleFitStepsRepository,
        calories_repository: GoogleFitCaloriesRepository,
        minutes_repository: GoogleFitMinutesRepository,
        feature_client: FeatureClientAsync
    ):
        self.__client = client
        self.__steps_repository = steps_repository
        self.__calories_repository = calories_repository
        self.__minutes_repository = minutes_repository
        self.__feature_client = feature_client

    async def upsert_calories(
        self,
        calories: List[GoogleFitDataPoint],
        get_selector: Callable
    ) -> None:
        '''
        Upsert Google Fit calories data

        `steps`: Google Fit query results
        `get_selector`: selector func for record key
        '''

        logger.info(f'Upserting {len(calories)} records')

        sync_tasks = DeferredTasks()
        for record in calories:
            sync_tasks.add_task(
                self.__calories_repository.upsert(
                    filter=get_selector(record),
                    replacement=record.to_dict()))

        await sync_tasks.run()

    async def upsert_minutes(
        self,
        minutes: List[GoogleFitDataPoint],
        get_selector: Callable
    ) -> None:
        '''
        Upsert Google Fit minutes data

        `steps`: Google Fit query results
        `get_selector`: selector func for record key
        '''

        logger.info(f'Upserting {len(minutes)} records')

        sync_tasks = DeferredTasks()
        for record in minutes:
            sync_tasks.add_task(
                self.__minutes_repository.upsert(
                    filter=get_selector(record),
                    replacement=record.to_dict()))

        await sync_tasks.run()

    async def upsert_steps(
        self,
        steps: List[GoogleFitDataPoint],
        get_selector: Callable
    ) -> None:
        '''
        Upsert Google Fit steps data

        `steps`: Google Fit query results
        `get_selector`: selector func for record key
        '''

        logger.info(f'Upserting {len(steps)} records')

        sync_tasks = DeferredTasks()
        for record in steps:
            sync_tasks.add_task(
                self.__steps_repository.upsert(
                    filter=get_selector(record),
                    replacement=record.to_dict()))

        await sync_tasks.run()

    async def aggregate_query(
        self,
        data_source: GoogleFitDataType,
        value_type: GoogleFitValueType,
        request: GoogleFitRequest
    ):
        '''
        Execute a Google Fit aggregate query
        on a given dataset
        '''

        logger.info(f'Query data source: {data_source.name}')
        logger.info(f'Start date: {request.start_timestamp}')
        logger.info(f'End date: {request.end_timestamp}')

        # Group the aggregate dataset by timedelta value
        group_by = timedelta(seconds=60 * 60)

        # Create the dataset aggregate query
        aggregate_query = FitAggregateDataset(
            start_timestamp=request.start_timestamp,
            end_timestamp=request.end_timestamp,
            aggregates=[data_source],
            groupby_time=group_by)

        # Send Google Fit request
        expended_calories = await self.__client.get_dataset_aggregate(
            query=aggregate_query.to_dict())

        return self.__handle_response(
            data=expended_calories,
            value_type=value_type)

    def __handle_response(
        self,
        data: dict,
        value_type: GoogleFitValueType
    ):
        '''
        Handle Google Fit query response

        `data`: raw query response
        `value_type`: the query response
        value data type
        '''

        # Bucketed results in response data
        values = data.get('bucket')

        dataset = [
            GoogleFitDataPoint(
                data=point,
                value_type=value_type
            ) for point in values
        ]

        # Remove records where value is 0
        # return where(
        #     dataset,
        #     lambda p: p.value > 0)

        return dataset

    async def get_steps(
        self,
        req: GoogleFitRequest
    ) -> List[GoogleFitDataPoint]:
        '''
        Get steps from Google Fit client

        `req`: request model
        '''

        logger.info(f'Get steps from Google Fit')

        return await self.aggregate_query(
            data_source=GoogleFitDataSource.Steps,
            value_type=GoogleFitValueType.Int,
            request=req)

    async def get_calories_expended(
        self,
        req: GoogleFitRequest
    ) -> List[GoogleFitDataPoint]:
        '''
        Get calories from Google Fit client

        `req`: request model
        '''

        logger.info(f'Get expended calories from Google Fit')

        aggregate = await self.aggregate_query(
            data_source=GoogleFitDataSource.ExpendedCalories,
            value_type=GoogleFitValueType.Float,
            request=req)

        return aggregate

    async def get_active_minutes(
        self,
        req: GoogleFitRequest
    ) -> List[GoogleFitDataPoint]:
        '''
        Get active minutes from Google Fit 
        client

        `req`: request model
        '''

        logger.info(f'Get expended calories from Google Fit')

        return await self.aggregate_query(
            data_source=GoogleFitDataSource.ActiveMinutes,
            value_type=GoogleFitValueType.Int,
            request=req)

    async def get_combined_fitness_data(
        self,
        start_date: str,
        end_date: str
    ):
        '''
        Get the combined Google Fit data for frontend
        display (steps, minutes and calories)

        `start_date`: start date as a parsable datetime
        string

        `end_date`: end date as a parsable datetime string
        '''

        timestamp_filter = TimestampRangeFilter(
            start_date=start_date,
            end_date=end_date).get_filter()

        logger.info(f'Date filter: {timestamp_filter}')

        # Query stored fitness data in parallel
        fetch = DeferredTasks(
            self.__calories_repository.query(timestamp_filter),
            self.__minutes_repository.query(timestamp_filter),
            self.__steps_repository.query(timestamp_filter))

        calories, minutes, steps = await fetch.run()

        return {
            'calories': self.__group_by_day(calories),
            'minutes': self.__group_by_day(minutes),
            'steps': self.__group_by_day(steps)
        }

    def __group_by_day(
        self,
        data
    ) -> List[Dict]:

        # Limit columns to timestamp and value
        df = pd.DataFrame(data)[['timestamp', 'value']]

        # Group by timestamp and sum value
        grouped = df.groupby('timestamp').sum()

        # Reset index, create new dataframe
        df = grouped.reset_index()

        # Get truncated date from timestamp
        df['date'] = df['timestamp'].apply(
            lambda x: datetime.fromtimestamp(x).strftime('%Y-%m-%d'))

        return df.to_dict(orient='records')
