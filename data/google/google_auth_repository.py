from framework.data.mongo_repository import MongoRepositoryAsync


class GoogleAuthRepository(MongoRepositoryAsync):
    def __init__(self, container=None):
        self.initialize(
            container=container,
            database='Google',
            collection='Auth')
