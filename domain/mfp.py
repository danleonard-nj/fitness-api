import json
from datetime import datetime, timedelta
from typing import List

from dateutil import parser
from framework.crypto.hashing import sha256
from framework.logger import get_logger
from framework.serialization import Serializable

logger = get_logger(__name__)


class MyFitnessPal:
    BaseUrl = 'https://www.myfitnesspal.com'
    DateFormat = '%Y-%m-%d'
    CredentialFile = 'myfitnesspal.json'


class MfpDateUtility:
    def from_string(self, date: str):
        return parser.parse(date).strftime(MyFitnessPal.DateFormat)

    def from_date(self, date: datetime):
        return date.strftime(MyFitnessPal.DateFormat)

    def get_range(self, start: datetime, days) -> List[datetime]:
        results = []

        for i in range(days):
            day = start - timedelta(days=i)
            results.append(day)

        return results


class DiaryRecord(Serializable):
    @property
    def timestamp(
        self
    ) -> int:
        '''
        Get a timestamp of day start
        '''
        date = parser.parse(self.date)
        return round(datetime(
            year=date.year,
            month=date.month,
            day=date.day).timestamp())

    def __init__(self, date, data: str):
        self.key = sha256(date)
        self.date = date
        self.data = data

    def get_selector(self):
        return {
            'key': self.key
        }

    def get_hash(self):
        return sha256(json.dumps(self, default=str))

    def to_dict(self):
        return super().to_dict() | {
            'timestamp': self.timestamp
        }

    @staticmethod
    def from_document(document):
        return DiaryRecord(
            data=document.get('data'),
            date=document.get('date'))


class NutritionEntry(Serializable):
    def __init__(self, data):
        self.fat = data.get('fat')
        self.sodium = data.get('sodium')
        self.carbs = data.get('carbohydrates')
        self.fiber = data.get('fiber')
        self.sugar = data.get('sugar')
        self.protein = data.get('protein')
        self.calories = data.get('energy').get('value')


class JournalEntry(Serializable):
    def __init__(self, data):
        self.id = data.get('id')
        self.meal_name = data.get('meal_name')

        food = data.get('food')

        self.brand_name = food.get('brand_name')
        self.description = food.get('description')

        serving_size = food.get('serving_sizes')
        unit, serving = self.get_serving_info(
            serving_size=serving_size)

        self.serving_size = serving
        self.serving_unit = unit
        self.quantity = data.get('servings')

        self.nutrition = NutritionEntry(
            data=data.get('nutritional_contents'))

        self.calories = self.nutrition.calories

    def get_serving_info(self, serving_size):
        if not any(serving_size):
            return None, None

        data = serving_size[0]

        return (
            data.get('unit'),
            data.get('value')
        )

    def to_dict(self):
        return super().to_dict() | {
            'nutrition': self.nutrition.to_dict()
        }


class DailyJournalRecord(Serializable):
    def __init__(self, record: List[dict]):
        self.key = record.get('key')
        self.date = record.get('timestamp')
        self.entries = self.create_record(
            data=record.get('data'))

    def create_record(self, data: List[dict]) -> List[JournalEntry]:
        entries = []
        for item in data:
            entry = JournalEntry(
                data=item)
            entries.append(entry)
        return entries

    def to_dict(self):
        return super().to_dict() | {
            'entries': [
                item.to_dict() for item
                in self.entries
            ]
        }


class DailySummaryRecord(Serializable):
    def __init__(self, record):
        self.total_calories = 0
        self.date = record.get('date')
        self.timestamp = record.get('timestamp')

        self.entries = []

        self.create_record(
            data=record.get('data'))

    def create_record(self, data):
        for item in data:
            if item == 'error':
                logger.info(f'Encountered error in journal record: {item}')
                continue
            entry = JournalEntry(data=item)
            self.total_calories += entry.calories
            self.entries.append({
                'name': entry.description,
                'serving': entry.serving_unit,
                'quantity': entry.quantity,
                'calories': entry.calories
            })


class MyFitnessPalSyncResult(Serializable):
    def __init__(self, data):
        self.key = data.get('key')
        self.date = data.get('date')
        self.items = len(data.get(
            'data', []))
