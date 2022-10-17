from datetime import datetime, timedelta
from typing import Dict

import pandas as pd
from dateutil import parser
from framework.logger.providers import get_logger
from framework.serialization import Serializable
from utilities.utils import UnitConverter

logger = get_logger(__name__)


class FitnessConfig(Serializable):
    def __init__(
        self,
        data
    ):
        '''
        Fitness config details

        `data`: config detail database record
        '''

        self.configuration_id = data.get('configuration_id')
        self.is_active = data.get('is_active')
        self.modified_date = data.get(
            'modified_date') or datetime.utcnow().isoformat()
        self.created_date = data.get(
            'created_date') or datetime.utcnow().isoformat()

        self.height = data.get('height')
        self.date_of_birth = data.get('date_of_birth')
        self.target_weight = data.get('target_weight')
        self.deficits = data.get('deficits')

    def get_date_of_birth(
        self
    ) -> datetime:
        return parser.parse(self.date_of_birth)


class FitnessCalculator:
    @classmethod
    def calculate_bmr_from_config(
        cls,
        weight: float,
        config: FitnessConfig
    ):
        return cls.calculate_bmr(
            weight=weight,
            dob=config.get_date_of_birth(),
            height_inches=config.height)

    @classmethod
    def calculate_bmr(
        cls,
        weight: float,
        dob: datetime,
        height_inches: int
    ):
        height_cm = UnitConverter.inch_to_cm(
            inches=height_inches)
        age = UnitConverter.days_old(
            date=dob)

        return (10 * weight + 6.25 * height_cm - 5 * age + 5)

    @classmethod
    def calculate_tdee(cls, bmr: int):
        activity_levels = ActivityLevelType.get_types()

        def to_description(level): return {
            'name': level.name,
            'description': level.description,
            'kcals': round(bmr * level.multiplier)
        }

        return [
            to_description(level)
            for level in activity_levels
        ]


class FitnessData(Serializable):
    def __init__(self, mfp, fitindex, google_fit):
        self.my_fitness_pal = mfp
        self.fitindex = fitindex
        self.google_fit = google_fit

    def to_dict(self):
        return {
            'my_fitness_pal': self.my_fitness_pal,
            'fitindex': self.fitindex,
            'google_fit': self.google_fit
        }

    def get_latest_weight(self) -> str:
        df = pd.DataFrame(self.fitindex)
        df.sort_values(by='date', ascending=False)

        return df.loc[0, 'date']


class FitnessTarget:
    def __init__(self, data):
        self.target = data.get('target')
        self.scope_days = data.get('scope_days')
        self.target_type = data.get('target_type')
        self.params = data.get('params')

    def get_date_range(self):
        end = datetime.now()
        start = (datetime.now() - timedelta(
            days=self.scope_days * -1))

        return start, end


class ActivityLevel:
    def __init__(self, name, multiplier, description):
        self.name = name
        self.multiplier = multiplier
        self.description = description


class ActivityLevelDescription:
    SEDENTARY = 'Little or no exercise'
    LIGHTLY_ACTIVE = 'Light exercise (3 - 5 days/week)'
    MODERATELY_ACTIVE = 'Moderate exercise (3 - 5 days/week)'
    VERY_ACTIVE = 'Hard exercise (6 - 7 days/week)'
    EXTRA_ACTIVE = 'Hard exercise (6 - 7 days/week) plus physical job'


class ActivityLevelType:
    SEDENTARY = ActivityLevel(
        name='Sedentary',
        multiplier=1.2,
        description=ActivityLevelDescription.SEDENTARY)

    LIGHTLY_ACTIVE = ActivityLevel(
        name='Lightly active',
        multiplier=1.375,
        description=ActivityLevelDescription.LIGHTLY_ACTIVE)

    MODERATELY_ACTIVE = ActivityLevel(
        name='Moderately active',
        multiplier=1.550,
        description=ActivityLevelDescription.MODERATELY_ACTIVE)

    VERY_ACTIVE = ActivityLevel(
        name='Very active',
        multiplier=1.725,
        description=ActivityLevelDescription.VERY_ACTIVE)

    EXTRA_ACTIVE = ActivityLevel(
        name='Extra active',
        multiplier=1.9,
        description=ActivityLevelDescription.EXTRA_ACTIVE)

    @classmethod
    def get_types(cls):
        return [
            cls.SEDENTARY,
            cls.LIGHTLY_ACTIVE,
            cls.MODERATELY_ACTIVE,
            cls.VERY_ACTIVE,
            cls.EXTRA_ACTIVE
        ]

    @classmethod
    def get_map(cls) -> Dict[str, ActivityLevel]:
        return {
            k: v for k, v in cls.__dict__
            if not k.startswith('__')
        }

    @classmethod
    def from_key(cls, key):
        return cls.get_map()[key]


class FitnessTargetType:
    GENERAL_WEIGHT = 1
    DATE_DEFICIT = 2


class GeneralWeightTarget(FitnessTarget):
    def __init__(self, data):
        super().__init__(data)

    def calculate(self, data: FitnessData, config: FitnessConfig):
        logger.info(f'Calculating general weight target')

        deficits = self.params.get('deficits')
        logger.info(f'Deficit parameters: {deficits}')

        if not any(data.fitindex):
            raise Exception(
                f'Could not fetch latest weight, no record available')

        latest_weight = data.get_latest_weight()
        latest_bmr = self.get_bmr(
            personal_data=config.personal_data,
            weight=latest_weight)

        logger.info(f'Latest weight: {latest_weight}')
        logger.info(f'Latest BMR: {latest_bmr}')

        activity_levels = ActivityLevelType.get_types()

        for deficit in deficits:
            logger.info(f'Calculating target at deficit: {deficit}')

            for level in activity_levels:
                logger.info(f'Calcluating target at activity level')

            result_weight = int(latest_weight)


class DateDeficitTarget(FitnessTarget):
    def __init__(self, data):
        super().__init__(data)
