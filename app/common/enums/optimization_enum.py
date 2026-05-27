from enum import Enum

class TypeOptimizationEnum(str, Enum):
    GRAPHICAL = "graphical"
    TWO_STEPS = "two_steps"


class OptimizationEnum(str, Enum):
    MAX = "MAX"
    MIN = "MIN"


class OperatorEnum(str, Enum):
    LESS_EQUAL = "<="
    GREATER_EQUAL = ">="
    EQUAL = "="