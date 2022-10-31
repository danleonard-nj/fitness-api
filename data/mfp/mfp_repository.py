from framework.mongo.mongo_repository import MongoRepositoryAsync
from motor.motor_asyncio import AsyncIOMotorClient


class MyFitnessPalRepository(MongoRepositoryAsync):
    def __init__(
        self,
        client: AsyncIOMotorClient
    ):
        super().__init__(
            client=client,
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
