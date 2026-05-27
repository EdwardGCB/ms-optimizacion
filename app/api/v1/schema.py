"""
Core schemas
"""
# Pydantic
from pydantic import BaseModel
from typing import Any


class SuccessResponse(BaseModel):
    data: Any


class ErrorSchema(BaseModel):
    internal_error: str
    description: str

    class Config:
        json_schema_extra = {
            "example": {
                "internal_error": "An error has occurred, contact your provider",
                "description": "Exception raised"
            }
        }


class ErrorResponse(BaseModel):
    error: ErrorSchema
