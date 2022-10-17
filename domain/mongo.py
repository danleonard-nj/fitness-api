from dateutil import parser


class TimestampRangeFilter:
    def __init__(
        self,
        start_date: str,
        end_date: str
    ):
        self.__start_date = start_date
        self.__end_date = end_date

    @property
    def start_timestamp(self):
        return round(parser.parse(
            self.__start_date).timestamp())

    @property
    def end_timestamp(self):
        return round(parser.parse(
            self.__end_date).timestamp())

    def get_filter(
        self
    ) -> dict:

        return {
            'timestamp': {
                '$lt': self.end_timestamp,
                '$gte': self.start_timestamp
            }
        }
