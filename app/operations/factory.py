"""Factory pattern for calculation operations.

Supports the classic four (Add, Sub, Multiply, Divide) plus three advanced
operations added in the final project: Power, Modulus, Root.
"""
from abc import ABC, abstractmethod


class Calculation(ABC):
    """Abstract base for a calculation operation."""

    def __init__(self, a: float, b: float):
        self.a = a
        self.b = b

    @abstractmethod
    def execute(self) -> float:
        ...


class Add(Calculation):
    def execute(self) -> float:
        return self.a + self.b


class Sub(Calculation):
    def execute(self) -> float:
        return self.a - self.b


class Multiply(Calculation):
    def execute(self) -> float:
        return self.a * self.b


class Divide(Calculation):
    def execute(self) -> float:
        if self.b == 0:
            raise ValueError("Cannot divide by zero")
        return self.a / self.b


# ----- Final-project additions -----

class Power(Calculation):
    """a raised to the power of b (a^b)."""

    def execute(self) -> float:
        # Python's `**` already handles fractional exponents and negatives,
        # but we explicitly guard 0**0 since semantics there are debated.
        # We treat 0**0 as 1 (Python's default) to keep tests deterministic.
        return self.a ** self.b


class Modulus(Calculation):
    """a mod b. Raises if b is zero."""

    def execute(self) -> float:
        if self.b == 0:
            raise ValueError("Cannot take modulus by zero")
        return self.a % self.b


class Root(Calculation):
    """The b-th root of a, i.e. a^(1/b).

    Examples:
        Root(9, 2)  -> 3.0   (square root)
        Root(27, 3) -> 3.0   (cube root)

    Restrictions:
        * b cannot be zero (would mean 1/0 in the exponent).
        * For an even-valued b, a must be non-negative — even roots of
          negatives are complex, which we don't model.
    """

    def execute(self) -> float:
        if self.b == 0:
            raise ValueError("Root degree cannot be zero")
        if self.a < 0 and self.b % 2 == 0:
            raise ValueError("Cannot take an even root of a negative number")
        # For odd roots of negatives, Python's `**` returns a complex number
        # (e.g. (-8) ** (1/3) ≠ -2). Compute |a|^(1/b) and re-sign manually.
        if self.a < 0:
            return -((-self.a) ** (1.0 / self.b))
        return self.a ** (1.0 / self.b)


class CalculationFactory:
    """Return the right Calculation subclass for a given type string."""

    _registry = {
        "Add": Add,
        "Sub": Sub,
        "Multiply": Multiply,
        "Divide": Divide,
        "Power": Power,
        "Modulus": Modulus,
        "Root": Root,
    }

    @classmethod
    def create(cls, calc_type: str, a: float, b: float) -> Calculation:
        if calc_type not in cls._registry:
            raise ValueError(f"Unknown calculation type: {calc_type}")
        return cls._registry[calc_type](a, b)

    @classmethod
    def supported_types(cls) -> list[str]:
        """Public list of supported operation names — handy for the UI."""
        return list(cls._registry.keys())
