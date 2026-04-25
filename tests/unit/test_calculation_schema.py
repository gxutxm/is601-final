"""Unit tests for CalculationCreate / CalculationUpdate / CalculationRead / CalculationStats."""
from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.calculation import (
    CalculationCreate,
    CalculationRead,
    CalculationStats,
    CalculationUpdate,
)


# ---------- CalculationCreate ----------

def test_valid_create():
    payload = CalculationCreate(a=2, b=3, type="Add")
    assert payload.type == "Add"


def test_invalid_type_rejected():
    with pytest.raises(ValidationError):
        CalculationCreate(a=1, b=2, type="Bogus")


def test_divide_by_zero_rejected():
    with pytest.raises(ValidationError, match="Cannot divide by zero"):
        CalculationCreate(a=10, b=0, type="Divide")


def test_modulus_by_zero_rejected():
    with pytest.raises(ValidationError, match="Cannot take modulus by zero"):
        CalculationCreate(a=10, b=0, type="Modulus")


def test_root_zero_degree_rejected():
    with pytest.raises(ValidationError, match="Root degree cannot be zero"):
        CalculationCreate(a=9, b=0, type="Root")


def test_root_even_root_of_negative_rejected():
    with pytest.raises(ValidationError, match="even root of a negative"):
        CalculationCreate(a=-4, b=2, type="Root")


def test_root_odd_root_of_negative_accepted():
    # Cube root of negative should be allowed at the schema level
    payload = CalculationCreate(a=-8, b=3, type="Root")
    assert payload.a == -8


def test_power_accepts_zero_exponent():
    payload = CalculationCreate(a=5, b=0, type="Power")
    assert payload.b == 0


def test_create_schema_has_no_user_id():
    """user_id is derived from the JWT server-side, not accepted from clients."""
    assert "user_id" not in CalculationCreate.model_fields


# ---------- CalculationUpdate ----------

def test_update_all_fields_optional():
    upd = CalculationUpdate()
    assert upd.a is None and upd.b is None and upd.type is None


def test_update_partial_ok():
    upd = CalculationUpdate(type="Power")
    assert upd.type == "Power"


def test_update_modulus_by_zero_rejected():
    with pytest.raises(ValidationError, match="modulus by zero"):
        CalculationUpdate(type="Modulus", b=0)


# ---------- CalculationRead ----------

def test_read_from_attributes():
    class FakeCalc:
        id = 1
        a = 2.0
        b = 3.0
        type = "Power"
        result = 8.0
        user_id = 42
        created_at = datetime(2026, 1, 1, 12, 0, 0)

    read = CalculationRead.model_validate(FakeCalc())
    dumped = read.model_dump()
    assert dumped["type"] == "Power"
    assert dumped["result"] == 8.0


# ---------- CalculationStats ----------

def test_stats_empty_state():
    stats = CalculationStats(
        total=0, by_type={}, most_used_type=None,
        avg_a=None, avg_b=None, avg_result=None,
    )
    assert stats.total == 0
    assert stats.by_type == {}


def test_stats_populated():
    stats = CalculationStats(
        total=5,
        by_type={"Add": 3, "Power": 2},
        most_used_type="Add",
        avg_a=4.5,
        avg_b=2.0,
        avg_result=10.5,
    )
    assert stats.total == 5
    assert stats.most_used_type == "Add"
