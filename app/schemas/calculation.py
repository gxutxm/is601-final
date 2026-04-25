"""Pydantic schemas for the Calculation resource (Pydantic v2)."""
from datetime import datetime
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator

# Extended in the final project to include Power, Modulus, Root.
CalcType = Literal[
    "Add",
    "Sub",
    "Multiply",
    "Divide",
    "Power",
    "Modulus",
    "Root",
]


def _validate_operands(calc_type: str, a: float, b: float) -> None:
    """Shared validation for both create and update payloads."""
    if calc_type == "Divide" and b == 0:
        raise ValueError("Cannot divide by zero")
    if calc_type == "Modulus" and b == 0:
        raise ValueError("Cannot take modulus by zero")
    if calc_type == "Root":
        if b == 0:
            raise ValueError("Root degree cannot be zero")
        if a < 0 and b % 2 == 0:
            raise ValueError("Cannot take an even root of a negative number")


class CalculationCreate(BaseModel):
    """Payload for creating a new calculation.

    `user_id` is intentionally *not* on this schema — it's derived from the
    authenticated JWT so users can only create calculations for themselves.
    """

    a: float = Field(..., description="First operand")
    b: float = Field(..., description="Second operand")
    type: CalcType

    @model_validator(mode="after")
    def check_operands(self):
        _validate_operands(self.type, self.a, self.b)
        return self


class CalculationUpdate(BaseModel):
    """Partial-update payload for PUT /calculations/{id}."""

    a: Optional[float] = None
    b: Optional[float] = None
    type: Optional[CalcType] = None

    @model_validator(mode="after")
    def check_operands(self):
        # Only validate when we actually have all the pieces.
        if self.type is not None and self.a is not None and self.b is not None:
            _validate_operands(self.type, self.a, self.b)
        elif self.type is not None and self.b is not None:
            # type+b alone is enough to detect zero-divisor cases.
            _validate_operands(self.type, 0.0, self.b)
        return self


class CalculationRead(BaseModel):
    """Public-facing calculation representation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    a: float
    b: float
    type: str
    result: Optional[float]
    user_id: int
    created_at: datetime


# ----- Final project: stats endpoint -----

class CalculationStats(BaseModel):
    """Aggregate statistics about the current user's calculations."""

    total: int = Field(..., description="Total number of calculations")
    by_type: Dict[str, int] = Field(
        ..., description="Count of calculations per operation type"
    )
    most_used_type: Optional[str] = Field(
        None, description="The operation type used most often (None if total=0)"
    )
    avg_a: Optional[float] = Field(None, description="Average of all `a` operands")
    avg_b: Optional[float] = Field(None, description="Average of all `b` operands")
    avg_result: Optional[float] = Field(None, description="Average of all results")
