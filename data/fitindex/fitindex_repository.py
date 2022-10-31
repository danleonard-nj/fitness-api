from framework.mongo.mongo_repository import MongoRepositoryAsync
from motor.motor_asyncio import AsyncIOMotorClient


class FitIndexRepository(MongoRepositoryAsync):
    def __init__(
        self,
        client: AsyncIOMotorClient
    ):
        super().__init__(
            client=client,
            database='FitIndex',
            collection='Measurements')

    async def upsert(self, filter, document):
        return await self.collection.find_one_and_replace(
            filter=filter,
            replacement=document,
            upsert=True)

    async def get_latest(self):
        query = self.collection.find().sort(
            'timestamp', -1)

        return await query.limit(1).to_list(
            length=1)

    async def query(self, filter):
        return await self.collection.find(filter).to_list(
            length=None)
