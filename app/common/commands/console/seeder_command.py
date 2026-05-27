from app.common.commands.console.seeder.generate import Generate
from app.common.commands.console.seeder.execute import Execute


class Seed:

    @staticmethod
    async def generate(seedername):
        seeder = Generate()
        seeder.seedername = seedername
        return await seeder.run()

    @staticmethod
    async def execute():
        seeder = Execute()
        return await seeder.run()
