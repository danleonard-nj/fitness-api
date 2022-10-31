import uuid
from datetime import datetime

import pandas as pd
from data.fitness_repository import FitnessConfigRepository
from dateutil import parser
from domain.fitness import FitnessConfig, FitnessData
from domain.google import GoogleFitRequest
from clients.cache_client import CacheClientAsync
from framework.concurrency import DeferredTasks
from framework.crypto.hashing import sha256
from framework.logger.providers import get_logger
from framework.serialization import Serializable
from framework.serialization.utilities import serialize

from services.fitindex.fitindex_service import FitIndexService
from services.google.google_fit_service import GoogleFitService
from services.mfp.mfp_service import MyFitnessPalService

logger = get_logger(__name__)


def where(items, func):
    results = []
    for item in items:
        if func(item) is True:
            results.append(item)
    return results


class CalorieDeficitResult(Serializable):
    def __init__(
        self,
        deficits,
        average_deficit,
        total_deficit,
        total_lbs
    ):
        self.deficits = deficits
        self.average_deficit = average_deficit
        self.total_deficit = total_deficit
        self.total_lbs = total_lbs


class FitnessService:
    def __init__(
        self,
        mfp_service: MyFitnessPalService,
        fitindex_service: FitIndexService,
        fit_service: GoogleFitService,
        config_repository: FitnessConfigRepository,
        cache_client: CacheClientAsync
    ):
        self.__mfp_service = mfp_service
        self.__fitindex_service = fitindex_service
        self.__fit_service = fit_service
        self.__config_repository = config_repository
        self.__cache_client = cache_client

    def get_date_hash_key(self, date_str):
        date = self.truncate_date(date_str)
        return sha256(date)

    def truncate_date(self, date_str):
        date = parser.parse(date_str)
        return date.strftime('%Y-%m-%d')

    def get_day_timestamp(self, date_str):
        date = parser.parse(date_str)
        day = datetime(
            year=date.year,
            month=date.month,
            day=date.day)
        return round(day.timestamp())

    async def insert_fitness_config(
        self,
        data: dict
    ) -> FitnessConfig:
        logger.info('Inactivating existing configs')
        await self.__config_repository.inactivate_configs()

        config = FitnessConfig(
            data=data)

        config.created_date = datetime.now().isoformat()
        config.modified_date = datetime.now().isoformat()

        config.configuration_id = str(uuid.uuid4())
        logger.info(f'Configuration ID: {config.configuration_id}')

        result = await self.__config_repository.insert(
            document=config.to_dict())
        logger.info(f'Inserted entity ID: {result.inserted_id}')

        return config

    async def get_fitness_config(
        self
    ) -> FitnessConfig:
        logger.info(f'Fetching active configuration')
        data = await self.__config_repository.get({
            'is_active': True
        })

        if data is None:
            raise Exception('No active configuration exists')

        logger.info(f'Configuration: {serialize(data)}')
        config = FitnessConfig(
            data=data)

        return config

    def calculate_deltas(self, mfp, calories):
        # Create dataframes from domain models
        mfp_df = pd.DataFrame([
            record.to_dict()
            for record in mfp])

        google_df = pd.DataFrame([
            record.to_dict()
            for record in calories])

        # Truncate dataframe columns
        logger.info(f'Truncating dataframe columns')
        mfp_df = mfp_df[['date', 'total_calories']]
        google_df = google_df[['date', 'value']]

        # Generate key for MyFitnessPal data
        logger.info(f'Generating key for MFP dataframe')
        mfp_df['key'] = mfp_df['date'].apply(
            lambda x: self.get_date_hash_key(x))

        # Generate key, truncate dates and group Google Fit
        # data by key and date
        logger.info(f'Grouping and generating key for Google Fit dataframe')
        google_df['date'] = google_df['date'].apply(
            lambda x: self.truncate_date(x))

        google_df['key'] = google_df['date'].apply(
            lambda x: self.get_date_hash_key(x))

        google_df = google_df.groupby([
            'key',
            'date']).sum().reset_index()

        # Rename columns to avoid clashing during merge
        logger.info('Updating dataframe value column names')
        google_df = google_df.rename(columns={
            'value': 'fit'
        })

        mfp_df = mfp_df.rename(columns={
            'total_calories': 'mfp'
        })

        # Merge MyFitnessPal and Google Fit data
        logger.info('Merging for MFP and Google Fit')
        merged = google_df.merge(
            right=mfp_df,
            on='key',
            how='left')
        logger.info('Merge successful')

        # Truncate dataframe and merge onto dataframe
        # containing list of dates (from GoogleFit)
        dates = google_df[[
            'date',
            'key'
        ]]

        logger.info('Merging combined dataframe on date list')
        final = dates.merge(
            right=merged,
            how='left',
            on='key')
        logger.info('Merge successful')

        # Truncate final merged dataframe columns
        truncated_final = final[[
            'key',
            'date',
            'fit',
            'mfp'
        ]]

        # Calculate calorie deltas between Google Fit and
        # MyFitnesspal
        logger.info(f'Truncating columns and removing nulls')
        truncated_final['delta'] = (truncated_final['mfp'] -
                                    truncated_final['fit'])

        truncated_final = truncated_final[(
            ~truncated_final['mfp'].isna() &
            ~truncated_final['fit'].isna())]

        # Sort the final dataframe by date
        logger.info(f'Sorting combined dataframe by date')
        sorted_final = truncated_final.sort_values('date')

        # Create timestamp column for frontend charts
        logger.info('Generating timestamp column from date')
        sorted_final['timestamp'] = sorted_final['date'].apply(
            lambda x: self.get_day_timestamp(x))

        logger.info(f'Calorie deltas calculated successfully')
        return sorted_final.to_dict(orient='records')

    async def get_calorie_deficits(
        self,
        start_date: str,
        end_date: str
    ):
        logger.info('Get calorie deltas')
        logger.info(f'Range: {start_date} : {end_date}')

        # cached = await self.__cache_client.get_json(
        #     key=CacheKey.calorie_deltas(
        #         start_date=start_date,
        #         end_date=end_date))

        # if cached is not None:
        #     logger.info(f'Returning calorie deltas from cache')
        #     return cached

        logger.info('Calculating calorie deltas')
        fetch = DeferredTasks(
            self.__mfp_service.get_daily_summaries(
                start_date=start_date,
                end_date=end_date),
            self.__fit_service.get_calories_expended(
                req=GoogleFitRequest(
                    start_date=start_date,
                    end_date=end_date)))

        mfp, calories = await fetch.run()

        result = self.calculate_deltas(
            mfp=mfp,
            calories=calories)

        # Calculate total deficit over time period
        total_deficit = round(
            sum([
                record.get('delta', 0)
                for record in result
            ]), 2)

        # Get average deficit
        average_deficit = round(
            total_deficit / len(result), 2)

        # Get total pounds from defiict
        total_lbs = round(
            total_deficit / 3500, 2)

        # await self.__cache_client.set_json(
        #     key=CacheKey.calorie_deltas(
        #         start_date=start_date,
        #         end_date=end_date),
        #     value=result,
        #     ttl=5)

        return CalorieDeficitResult(
            deficits=result,
            average_deficit=average_deficit,
            total_deficit=total_deficit,
            total_lbs=total_lbs)

    async def get_combined_fitness_data(
        self,
        start: str,
        end: str
    ):

        logger.info(f'Fetching fitness data for range: {start} : {end}')

        # Fetch FitIndex, Google Fit and MyFitnessPal
        # data for requested range
        tasks = DeferredTasks(
            self.__mfp_service.get_daily_summaries(
                start_date=start,
                end_date=end),
            self.__fitindex_service.get_measurements(
                start_date=start,
                end_date=end),
            self.__fit_service.get_combined_fitness_data(
                start_date=start,
                end_date=end))

        mfp, fitindex, google_fit = await tasks.run()

        logger.info(f'Fitness data range fetched successfully')

        return FitnessData(
            mfp=mfp,
            fitindex=fitindex,
            google_fit=google_fit)
