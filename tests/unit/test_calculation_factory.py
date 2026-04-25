"""Unit tests for the CalculationFactory and individual operation classes."""
import math
import pytest

from app.operations.factory import (
    Add, Sub, Multiply, Divide,
    Power, Modulus, Root,
    CalculationFactory,
)


# ---------- Original four ----------

def test_add():
    assert Add(2, 3).execute() == 5


def test_sub():
    assert Sub(10, 4).execute() == 6


def test_multiply():
    assert Multiply(6, 7).execute() == 42


def test_divide():
    assert Divide(10, 2).execute() == 5


def test_divide_by_zero_raises():
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        Divide(10, 0).execute()


# ---------- Power ----------

def test_power_basic():
    assert Power(2, 10).execute() == 1024


def test_power_zero_exponent():
    assert Power(7, 0).execute() == 1


def test_power_negative_exponent():
    assert Power(2, -1).execute() == 0.5


def test_power_fractional_exponent():
    # 16 ** 0.5 == 4
    assert Power(16, 0.5).execute() == pytest.approx(4.0)


# ---------- Modulus ----------

def test_modulus_basic():
    assert Modulus(10, 3).execute() == 1


def test_modulus_zero_remainder():
    assert Modulus(12, 4).execute() == 0


def test_modulus_negative_dividend():
    # Python's % follows the sign of the divisor; -7 % 3 == 2
    assert Modulus(-7, 3).execute() == 2


def test_modulus_by_zero_raises():
    with pytest.raises(ValueError, match="Cannot take modulus by zero"):
        Modulus(10, 0).execute()


# ---------- Root ----------

def test_root_square():
    assert Root(9, 2).execute() == pytest.approx(3.0)


def test_root_cube():
    assert Root(27, 3).execute() == pytest.approx(3.0)


def test_root_fractional():
    # 16 ** (1/4) == 2
    assert Root(16, 4).execute() == pytest.approx(2.0)


def test_root_zero_degree_raises():
    with pytest.raises(ValueError, match="Root degree cannot be zero"):
        Root(9, 0).execute()


def test_root_even_root_of_negative_raises():
    with pytest.raises(ValueError, match="even root of a negative number"):
        Root(-4, 2).execute()


def test_root_odd_root_of_negative_ok():
    # Cube root of -8 should be -2 (odd roots of negatives are real)
    result = Root(-8, 3).execute()
    assert result == pytest.approx(-2.0, abs=1e-9)


# ---------- Factory ----------

def test_factory_returns_correct_class():
    assert isinstance(CalculationFactory.create("Add", 1, 2), Add)
    assert isinstance(CalculationFactory.create("Power", 1, 2), Power)
    assert isinstance(CalculationFactory.create("Modulus", 1, 2), Modulus)
    assert isinstance(CalculationFactory.create("Root", 1, 2), Root)


def test_factory_rejects_unknown_type():
    with pytest.raises(ValueError, match="Unknown calculation type"):
        CalculationFactory.create("Bogus", 1, 2)


def test_factory_supported_types_includes_new_ops():
    types = CalculationFactory.supported_types()
    assert "Add" in types
    assert "Power" in types
    assert "Modulus" in types
    assert "Root" in types
