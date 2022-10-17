import enum
import io
import uuid
from datetime import datetime, timedelta
from typing import List

import pytz
from framework.crypto.hashing import sha256
from framework.serialization import Serializable
from googleapiclient.http import MediaIoBaseUpload
from dateutil import parser

from google.oauth2.credentials import Credentials

from utilities.utils import MongoUtils


class GoogleDriveDirectory:
    PodcastDirectoryId = '1jvoXhIvGLAn5DV73MK3IbcfQ6EF-L3qm'


class GoogleFit:
    BaseUrl = 'https://www.googleapis.com/fitness'


class FitValueType:
    KEY = None
    DEFAULT = None


class IntValueType(FitValueType):
    KEY = 'intVal'
    DEFAULT = 0


class FloatValueType(FitValueType):
    KEY = 'fpVal'
    DEFAULT = 0


class GoogleFitValueType:
    Int = IntValueType()
    Float = FloatValueType()


class GoogleFitQueryType(enum.IntEnum):
    ActiveMinutes = 1
    CaloriesExpended = 2
    Steps = 3

    @classmethod
    def from_name(cls, value):
        return cls[value].value


def first(items, func=None):
    if func is None:
        if any(items):
            return items[0]

    for item in items:
        if func(item):
            return item
    return None


def is_dict(value):
    return isinstance(value, dict)


class GoogleAuthClient(Serializable):
    def __init__(self, data):
        self.client_id = data.get('client_id')
        self.client_name = data.get('client_name')
        self.credentials = data.get('credentials')
        self.scopes = data.get('scopes')
        self.error = data.get('error')
        self.created_date = data.get('created_date')
        self.last_refresh = data.get('last_refresh')

    def get_selector(self):
        return {
            'client_name': self.client_name
        }

    def new_client(self):
        self.client_id = str(uuid.uuid4())
        self.created_date = datetime.now().isoformat()

    def get_google_creds(self, scopes=None) -> Credentials:
        creds = Credentials.from_authorized_user_info(
            self.credentials,
            scopes or self.scopes)

        return creds


class GoogleTokenResponse(Serializable):
    def __init__(self, creds: Credentials):
        self.token = creds.token
        self.id_token = creds.id_token
        self.scopes = creds.scopes
        self.valid = creds.valid
        self.expiry = creds.expiry.isoformat()


class GoogleFitDataType(Serializable):
    def __init__(self, id, name):
        self.id = id
        self.name = name

    def to_dict(self):
        return {
            'dataTypeName': self.name,
            'dataSourceId': self.id
        }


class GoogleFitDataSource:
    Steps = GoogleFitDataType(
        id='derived:com.google.step_count.delta:com.google.android.gms:estimated_steps',
        name='com.google.step_count.delta')

    ExpendedCalories = GoogleFitDataType(
        id='derived:com.google.calories.expended:com.google.android.gms:merge_calories_expended',
        name='com.google.calories.expended')

    ActiveMinutes = GoogleFitDataType(
        id='derived:com.google.active_minutes:com.google.android.gms:merge_active_minutes',
        name='com.google.active_minutes')


class FitAggregateDataset(Serializable):
    def __init__(
        self,
        start_timestamp: int,
        end_timestamp: int,
        aggregates: List[GoogleFitDataType],
        groupby_time: timedelta
    ):
        self.__start_timestamp = start_timestamp
        self.__end_timestamp = end_timestamp
        self.__aggregates = aggregates
        self.__groupby_time = groupby_time

    def __seconds_to_milliseconds(self, seconds):
        return int(seconds * 1000)

    @property
    def start_timestamp(self):
        return self.__seconds_to_milliseconds(
            seconds=self.__start_timestamp)

    @property
    def end_timestamp(self):
        return self.__seconds_to_milliseconds(
            seconds=self.__end_timestamp)

    @property
    def aggregates(self):
        return [
            agg.to_dict() for agg
            in self.__aggregates
        ]

    @property
    def groupby_time(self):
        return self.__seconds_to_milliseconds(
            seconds=self.__groupby_time.total_seconds())

    def to_dict(self):
        return {
            'aggregateBy': self.aggregates,
            'startTimeMillis': self.start_timestamp,
            'endTimeMillis': self.end_timestamp,
            'bucketByTime': {
                'durationMillis': self.groupby_time
            }
        }


class GoogleFitRequest:
    def __init__(
        self,
        start_date: str,
        end_date: str
    ):
        self.__start_date = start_date
        self.__end_date = end_date

    @property
    def start_timestamp(
        self
    ) -> datetime:
        return round(parser.parse(
            self.__start_date).timestamp())

    @property
    def end_timestamp(
        self
    ) -> datetime:
        return round(parser.parse(
            self.__end_date).timestamp())


class GoogleFitDataPoint(Serializable):
    def __init__(
        self,
        data: dict,
        value_type: FitValueType
    ):
        self.__value_type = value_type

        dataset = data.get('dataset', [])[0]
        point = dataset.get('point', {})

        self.__data_source = dataset.get('dataSourceId')
        self.__end_time = data.get('endTimeMillis')
        self.__start_time = data.get('startTimeMillis')

        self.__values = (
            [] if not any(point)
            else point[0].get('value')
        )

    def __milliseconds_to_datetime(
        self,
        milliseconds
    ):
        timezone = pytz.timezone('America/Phoenix')
        seconds = int(round(milliseconds / 1000))
        return datetime.fromtimestamp(
            seconds).astimezone(timezone)

    @property
    def start_date(self):
        return self.__milliseconds_to_datetime(
            milliseconds=int(self.__start_time))

    @property
    def end_date(self):
        return self.__milliseconds_to_datetime(
            milliseconds=int(self.__end_time))

    @property
    def value_type(self):
        return self.__value_type

    @property
    def data_source(self):
        return self.__data_source

    @property
    def data_type(self):
        return self.__data_type

    @property
    def value(self):
        if any(self.__values) and is_dict(first(self.__values)):
            return first(self.__values).get(self.__value_type.KEY)
        return self.__value_type.DEFAULT

    @property
    def key(self):
        return sha256(
            str({
                'year': self.start_date.year,
                'month': self.start_date.month,
                'day': self.start_date.day,
                'hour': self.start_date.hour
            })
        )

    @property
    def timestamp(self):
        timezone = pytz.timezone('America/Phoenix')
        date = datetime(
            year=self.start_date.year,
            month=self.start_date.month,
            day=self.start_date.day,
            hour=0,
            minute=0,
            second=0).astimezone(timezone)

        return round(date.timestamp())

    def to_dict(self):
        return {
            'key': self.key,
            'date': self.start_date.isoformat(),
            'timestamp': self.timestamp,
            'data_source': self.data_source,
            'value': self.value
        }


class GoogleDriveFileUpload:
    @property
    def data(self):
        return self.__data

    @property
    def metadata(self):
        return self.__metadata

    @property
    def media(self):
        return self.__get_media_io()

    def __init__(
        self,
        filename,
        data,
        mimetype,
        resumable=True,
        parent_directory=None
    ):
        self.__mimetype = mimetype
        self.__resumable = resumable
        self.__data = self.__get_stream(
            data=data)

        self.__metadata = self.__get_metadata(
            filename=filename,
            parent_directory=parent_directory)

    def __get_stream(
        self,
        data: bytes
    ) -> io.BytesIO:
        file = io.BytesIO(data)
        file.seek(0)

        return file

    def __get_media_io(self):
        return MediaIoBaseUpload(
            self.__data,
            mimetype=self.__mimetype,
            resumable=self.__resumable)

    def __get_metadata(
        self,
        filename: str,
        parent_directory: str
    ):
        file_metadata = {
            'name': filename,
        }

        if parent_directory is not None:
            file_metadata['parents'] = [
                parent_directory]

        return file_metadata

    def __exit__(self, *args, **kwargs):
        if not self.__data.closed:
            self.__data.close()


class GoogleFitCombinedData(Serializable):
    def __init__(self, minutes, calories, steps):
        self.steps = steps
        self.calories = calories
        self.minutes = minutes
