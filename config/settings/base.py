from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from app.common.models.list import model_list
from config.settings.settings import settings

API_VERSION = "v1.0.0"


async def connect_db(is_test: bool = False):

    uri = settings.mongo_uri_test if is_test else settings.mongo_uri
    db_name = settings.mongo_db_test if is_test else settings.mongo_db

    client = AsyncIOMotorClient(uri)

    await init_beanie(
        database=client[db_name],
        document_models=model_list
    )
