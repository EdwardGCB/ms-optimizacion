from paver.easy import task, cmdopts
import asyncio

from app.common.commands.console.seeder_command import Seed
from app.common.models.list import model_list
from app.common.commands.tasks.exceptions import SeederMissingNameException
from config.settings.base import connect_db


@task
@cmdopts([
    ('seeder=', 's', 'The class name of the root seeder')
])
def generate(options):
    '''Generate new seeders to be executed'''
    try:
        if not hasattr(options, "seeder"):
            raise SeederMissingNameException()
    except Exception as err:
        print(err)


async def async_execute_seeders(options={}, is_test=False):
    '''Execute created seeders into the database'''
    try:
        await connect_db(is_test)

        if hasattr(options, "rewrite"):
            for model in model_list:
                await model().drop()

        seeder = Seed()
        return await seeder.execute()
    except Exception as err:
        print(err)


@task
@cmdopts([
    ('rewrite', 'r', 'Rewrite seeders')
])
def execute(options):
    '''Execute created seeders into the database'''
    asyncio.run(async_execute_seeders(options))
