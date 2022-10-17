from framework.data.mongo_repository import MongoRepositoryAsync


class GoogleFitCaloriesRepository(MongoRepositoryAsync):
    def __init__(self, container=None):
        self.initialize(
            container=container,
            database='Google',
            collection='Calories')

    async def upsert(self, filter, replacement):
        return await self.collection.find_one_and_replace(
            filter=filter,
            replacement=replacement,
            upsert=True)

    async def query(self, filter):
        return await self.collection.find(
            filter).to_list(length=None)
