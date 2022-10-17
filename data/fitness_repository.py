from framework.data.mongo_repository import MongoRepositoryAsync
from framework.concurrency.concurrency import DeferredTasks


class FitnessConfigRepository(MongoRepositoryAsync):
    def __init__(self, container=None):
        self.initialize(
            container=container,
            database='Fitness',
            collection='Config')

    async def inactivate_configs(self):
        def get_selector(x): return {
            'configuration_id': x.get('configuration_id')
        }

        configs = await self.get_all()

        tasks = DeferredTasks()
        for config in configs:
            config['is_active'] = False
            tasks.add_task(self.replace(
                selector=get_selector(config),
                document=config))

        await tasks.run()
