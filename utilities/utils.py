from typing import Union
from dateutil import parser
from dateutil import relativedelta
from datetime import datetime
from framework.logger import get_logger

logger = get_logger(__name__)


class DateUtils:
    DATE_FORMAT = '%Y-%m-%d'

    @classmethod
    def relative_delta_string(cls, delta: relativedelta):
        return f'{delta.years} year(s) {delta.months} month(s) {delta.days} day(s)'

    @classmethod
    def parse(cls, datestr):
        return parser.parse(datestr)

    @classmethod
    def parse_timestamp(cls, datestr):
        date = parse(datestr)
        return int(date.timestamp())

    @classmethod
    def to_timestamp_day(cls, date: Union[str, datetime]):
        if date is None:
            raise Exception(f'Cannot create day timestamp from null')

        if isinstance(date, str):
            date = parser.parse(date)

        day = cls.to_date(
            _datetime=date)

        return int(day.timestamp())

    @classmethod
    def to_date(cls, _datetime: datetime):
        return datetime(
            year=_datetime.year,
            month=_datetime.month,
            day=_datetime.day)

    @classmethod
    def to_date_string(cls, _datetime: Union[str, datetime]):
        if isinstance(_datetime, str):
            _datetime = parser.parse(_datetime)

        return cls.to_date(
            _datetime=_datetime,
        ).strftime(cls.DATE_FORMAT)


class MongoUtils:
    @staticmethod
    def filter_range(start, end):
        return {'$lt': end, '$gte': start}


class UnitConverter:
    @staticmethod
    def inch_to_cm(inches):
        return (inches * 2.54)

    @staticmethod
    def days_old(date):
        delta = datetime.now() - date
        return round(delta.days / 365)


def get_value_map(_enum):
    return {
        v.value: k for k, v
        in _enum.__members__.items()
    }


def sort_by(items, key):
    if any(items):
        logger.info(f'Sort type: {type(items[0]).__name__}: Key: {key}')
        return sorted(items, key=lambda x: get_sort_key(x, key))


class CacheKey:
    @staticmethod
    def calorie_deltas(start_date, end_date):
        return f'calorie_delta-{start_date}-{end_date}'
