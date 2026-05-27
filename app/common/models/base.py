from beanie import Document
from pydantic import BaseModel, Field
from bson import ObjectId

from uuid import UUID
from datetime import datetime
from typing import List, Optional


class BaseDocument(Document):
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None

    async def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        await super().save(*args, **kwargs)

    @classmethod
    async def find_one_by_params(cls, params: dict = {}, exclude_trashed=True):
        """
        Finds a seed by its name.
        :param seed_name: The name of the seed.
        :return: The Seed document or None if not found.
        """
        filter_query = params
        if exclude_trashed:
            filter_query["deleted_at"] = None

        if "_id" in filter_query:
            filter_query["_id"] = ObjectId(filter_query["_id"])

        return await cls.find_one(filter_query, fetch_links=True)

    @classmethod
    async def find_many_by_params(cls, params: dict, exclude_trashed=True):
        """
        Finds a seed by its name.
        :param seed_name: The name of the seed.
        :return: The Seed document or None if not found.
        """
        filter_query = params
        if exclude_trashed:
            filter_query["deleted_at"] = None
        records_cursor = cls.find_all()
        return await records_cursor.to_list()


class BaseRuleStepModel(BaseModel):
    active: bool
    alias: str
    component: str
    settings: dict


class BaseRuleModel(BaseDocument):
    uuid: UUID
    version: int
    steps: List[BaseRuleStepModel]
    on_stop: Optional[List[BaseRuleStepModel]] = []
    on_error: List[BaseRuleStepModel]
