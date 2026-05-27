from datetime import datetime
from typing import List, Optional, Literal, Any

from beanie import Document
from pydantic import BaseModel, Field
from uuid import UUID, uuid4

class TableRow(BaseModel):
    label: str
    cb: Optional[float] = None
    basic_var: Optional[str] = None
    coefficients: List[float]
    bi: Optional[float] = None


class RowOperation(BaseModel):
    target: str
    expression: str
    factor: float
    source_rows: List[str]


class PivotInfo(BaseModel):
    column_index: int
    column_variable: str
    column_reason: str
    row_index: int
    row_label: str
    row_reason: str
    pivot_value: float


class Iteration(BaseModel):
    phase: Literal[1, 2]
    iteration: int
    description: str
    cj: List[float]
    variables: List[str]
    rows: List[TableRow]
    zj_cj: List[float]
    z: float
    pivot: Optional[PivotInfo] = None
    row_operations: List[RowOperation] = Field(default_factory=list)


class PhaseOneRestriction(BaseModel):
    original_operator: str
    operator: str = "="
    coefficients: List[float]
    bi: float
    added_vars: List[str] = Field(default_factory=list)
    text: str


class PhaseOneSetup(BaseModel):
    objective_text: str
    objective_coefficients: List[float]
    variables: List[str]
    restrictions: List[PhaseOneRestriction]


class PhaseTwoSetup(BaseModel):
    objective_text: str
    objective_coefficients: List[float]
    variables: List[str]
    removed_variables: List[str] = Field(default_factory=list)
    restrictions: List[PhaseOneRestriction]
    initial_basis: List[str] = Field(default_factory=list)


class TwoPhaseResult(BaseModel):
    status: Literal["optimal", "infeasible", "unbounded"]
    z: Optional[float] = None
    basis: List[str] = Field(default_factory=list)
    solution: dict = Field(default_factory=dict)
    phase_one_setup: Optional[PhaseOneSetup] = None
    phase_two_setup: Optional[PhaseTwoSetup] = None
    iterations: List[Iteration] = Field(default_factory=list)


class OptimizationModel(Document):
    payload: dict
    type_optimization: str
    result: dict
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "optimizations"
