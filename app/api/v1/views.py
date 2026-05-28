"""
Simplex & Two Phase views
"""

from fastapi import APIRouter, Query

from app.api.api_responser import ApiResponser
from app.api.v1.schema import ErrorResponse, SuccessResponse
from app.api.v1.serializer import (
    CreateOptimizationRequest,
    UpdateOptimizationRequest,
)

from app.api.core.handlers import OptimizationHandler
from app.common.enums.optimization_enum import TypeOptimizationEnum


router = APIRouter(prefix="/optimizations")

responses = {
    500: {"model": ErrorResponse},
    200: {"model": SuccessResponse},
}

# -----------------------------
# Process CRUD
# -----------------------------

@router.post("/", responses=responses)
async def create_optimization(payload: CreateOptimizationRequest):
    response = await OptimizationHandler.create(payload)
    return ApiResponser.success(response)


@router.get("/", responses=responses)
async def list_optimizations(
        page: int = Query(1, ge=1),
        limit: int = Query(10, ge=1, le=100),
):
    response = await OptimizationHandler.list(page, limit)
    return ApiResponser.success(response)


@router.get("/{optimization_type}/{optimization_uuid}", responses=responses)
async def get_optimization(optimization_type: TypeOptimizationEnum, optimization_uuid: str):
    response = await OptimizationHandler.get(optimization_type, optimization_uuid)
    return ApiResponser.success(response)


@router.put("/{optimization_uuid}", responses=responses)
async def update_optimization(optimization_uuid: str, payload: UpdateOptimizationRequest):
    response = await OptimizationHandler.update(optimization_uuid, payload)
    return ApiResponser.success(response)


@router.delete("/{optimization_uuid}", responses=responses)
async def delete_optimization(optimization_uuid: str):
    response = await OptimizationHandler.delete(optimization_uuid)
    return ApiResponser.success(response)
