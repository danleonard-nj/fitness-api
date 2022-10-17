from framework.data.mongo_repository import MongoRepositoryAsync


class MyFitnessPalRepository(MongoRepositoryAsync):
    def __init__(self, container=None):
        self.initialize(
            container=container,
            database='MyFitnessPal',
            collection='Diary')

    async def query(self, filter):
        return await self.collection.find(
            filter).to_list(length=None)

    async def upsert(self, filter, replacement):
        return await self.collection.find_one_and_replace(
            filter=filter,
            replacement=replacement,
            upsert=True)
