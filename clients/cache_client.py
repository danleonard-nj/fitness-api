import json
from typing import Iterable, Union

import aioredis
import redis
from framework.configuration.configuration import Configuration
from framework.logger.providers import get_logger
from framework.serialization.utilities import serialize

logger = get_logger(__name__)


class CacheClientAsync:
    def __init__(
        self,
        configuration: Configuration
    ):
        self.host = configuration.redis.get('host')
        self.port = configuration.redis.get('port')

        self.client = None

    async def get_client(self) -> aioredis.Redis:
        if self.client is None:
            self.client = aioredis.Redis(
                host=self.host,
                port=self.port)
        return self.client

    async def set_cache(self, key: str, value: str, ttl=60):
        '''
        Cache a string value at the specified cache key

        `key`: cache key
        `value`: cache value as `str`
        `ttl`: Cache time to live in minutes
        '''

        client = await self.get_client()

        await client.set(
            name=key,
            value=value,
            ex=(ttl * 60))

    async def set_json(self, key: str, value: Union[dict, Iterable], ttl: int = 60) -> None:
        '''
        Cache a serializable JSON value at the specified cache key

        `key`: cache key
        `value`: Serializable object to cache
        `ttl`: Time to live in minutes
        '''

        await self.set_cache(
            key=key,
            value=serialize(value),
            ttl=ttl)

    async def get_cache(self, key: str) -> Union[str, None]:
        '''
        Fetch a string value from cache and return value or `None` if no
        cached value exists

        `key`: cache key        
        '''

        client = await self.get_client()

        value = await client.get(name=key)
        if value is not None:
            return value.decode()

    async def get_json(self, key: str) -> Union[dict, Iterable, None]:
        '''
        Fetch a serialized cache value and return the deserialized object
        or `None` if no cached value exists

        `key`: the cache key
        '''

        value = await self.get_cache(
            key=key)

        if value is not None:
            return json.loads(value)

    async def delete_key(self, key: str) -> None:
        '''
        Delete a key from the cache

        `key`: cache key
        '''

        client = await self.get_client()

        await client.delete(key)
