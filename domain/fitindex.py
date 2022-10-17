
from datetime import datetime

from framework.crypto.hashing import sha256
from framework.logger.providers import get_logger
from framework.serialization import Serializable
from dateutil import parser

from utilities.utils import DateUtils

logger = get_logger(__name__)


class FitIndexConstants:
    DateFormat = '%Y-%m-%d'
    UserId = '1760541284271166510'
    AppRevision = '1.10.1'
    PhoneType = 'SM-N970U'
    SystemType = '11'
    Timezone = 'America/Phoenix'
    AreaCode = 'US'
    Locale = 'en'
    AppId = 'FITINDEX'
    Platform = 'android'
    SessionKey = 'c18f55c7-c12d-4976-9186-d2795dee9caa'


class FitIndexMeasurement(Serializable):
    @property
    def key(self):
        return sha256(self.date)

    @property
    def date(self):
        parsed = datetime.fromtimestamp(
            self.timestamp)

        date = datetime(
            year=parsed.year,
            month=parsed.month,
            day=parsed.day)

        return date.isoformat()

    @property
    def timestamp(self):
        return self.time_stamp

    def __init__(self, data):
        self.id = data.get('id')
        self.actual_resistance = data.get('actual_resistance')
        self.user_id = data.get('b_user_id')
        self.bmi = data.get('bmi')
        self.bmr = data.get('bmr')
        self.bodyage = data.get('bodyage')
        self.bodyfat = data.get('bodyfat')
        self.created_stamp = data.get('created_stamp')
        self.muscle = data.get('muscle')
        self.person_type = data.get('person_type')
        self.protein = data.get('protein')
        self.resistance = data.get('resistance')
        self.subfat = data.get('subfat')
        self.time_stamp = data.get('time_stamp')
        self.time_zone = data.get('time_zone')
        self.visfat = data.get('visfat')
        self.waistline = data.get('waistline')
        self.water = data.get('water')
        self.weight_kgs = data.get('weight')
        self.weight_lbs = self.to_lbs(data.get('weight') or 0)

    def get_selector(self):
        return {
            'key': self.key
        }

    def to_lbs(self, kg):
        return kg * 2.2046

    def calculate_bmr(self, weight):
        return (10 * weight + 6.25 * self.calculate_height()
                - 5 * self.calculate_age() + 5)

    def calculate_age(self):
        delta = datetime.now() - datetime(1994, 5, 25)
        return round(delta.days / 365)

    def calculate_height(self):
        return (6 * 12 * 2.54)

    def to_dict(self):
        return super().to_dict() | {
            'key': self.key,
            'date': self.date,
            'timestamp': self.time_stamp
        }


def lbs_to_kgs(lbs):
    return lbs / 2.2046


class MeasurementSummary(Serializable):
    def __init__(self, data):
        self.key = data.get('key')
        self.date = datetime.fromtimestamp(
            int(data.get('time_stamp'))).isoformat()
        self.timestamp = data.get('time_stamp')
        self.weight = data.get('weight_lbs')
        self.bmi = data.get('bmi')
        self.bmr = data.get('bmr')
        self.body_fat = data.get('bodyfat')
