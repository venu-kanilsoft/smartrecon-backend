import aioredis
import framework
import framework.settings
import framework.redispool

class _RedisQueue(object):
    """Simple Queue with Redis Backend"""
    def __init__(self, name, namespace='queue', **redis_kwargs):
        """The default connection parameters are: host='localhost', port=6379, db=0"""
        self.key = '%s:%s' % (namespace, name)
        # self.__db = await framework.redispool.get_redis_connection()

    @classmethod
    async def client(cls) -> aioredis.Redis:
        return await framework.redispool.get_redis_connection()

    async def qsize(self):
        """Return the approximate size of the queue."""
        client = await self.client()
        return await client.llen(self.key)

    async def empty(self):
        """Return True if the queue is empty, False otherwise."""
        return await self.qsize() == 0

    async def put(self, item):
        """Put item into the queue."""
        client = await self.client()
        await client.rpush(self.key, item)

    async def get(self, block=True, timeout=0):
        """Remove and return an item from the queue.

        If optional args block is true and timeout is None (the default), block
        if necessary until an item is available."""
        client = await self.client()
        if block:
            item = await client.blpop(self.key, timeout=timeout)
        else:
            item = await client.lpop(self.key)

        if item:
            item = item[1]
        return item

    async def get_nowait(self):
        """Equivalent to get(False)."""
        return await self.get(False)