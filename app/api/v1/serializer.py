from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from app.common.enums.optimization_enum import (
    TypeOptimizationEnum,
    OptimizationEnum,
    OperatorEnum,
)


class RestrictionRequest(BaseModel):
    coefficients: List[float] = Field(..., min_length=1)
    operator: OperatorEnum
    value: float


class CreateOptimizationRequest(BaseModel):
    nro_variables: int = Field(..., ge=1)
    nro_restrictions: int = Field(..., ge=1)
    type_optimization: TypeOptimizationEnum
    optimization: OptimizationEnum
    coefficients: List[float] = Field(..., min_length=1)
    restrictions: List[RestrictionRequest] = Field(..., min_length=1)

    @field_validator("coefficients")
    @classmethod
    def validate_coefficients_length(cls, v, info):
        nro_variables = info.data.get("nro_variables")
        if nro_variables is not None and len(v) != nro_variables:
            raise ValueError(
                f"coefficients debe tener {nro_variables} elementos, recibió {len(v)}"
            )
        return v

    @field_validator("restrictions")
    @classmethod
    def validate_restrictions(cls, v, info):
        nro_restrictions = info.data.get("nro_restrictions")
        nro_variables = info.data.get("nro_variables")

        if nro_restrictions is not None and len(v) != nro_restrictions:
            raise ValueError(
                f"restrictions debe tener {nro_restrictions} elementos, recibió {len(v)}"
            )

        if nro_variables is not None:
            for idx, r in enumerate(v):
                if len(r.coefficients) != nro_variables:
                    raise ValueError(
                        f"restriction[{idx}].coefficients debe tener {nro_variables} elementos"
                    )
        return v


class UpdateOptimizationRequest(BaseModel):
    nro_variables: Optional[int] = Field(None, ge=1)
    nro_restrictions: Optional[int] = Field(None, ge=1)
    type_optimization: Optional[TypeOptimizationEnum] = None
    optimization: Optional[OptimizationEnum] = None
    coefficients: Optional[List[float]] = Field(None, min_length=1)
    restrictions: Optional[List[RestrictionRequest]] = Field(None, min_length=1)