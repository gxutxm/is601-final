"""Integration tests for the Calculation model against Postgres."""
import pytest

from app.models.user import User
from app.models.calculation import Calculation
from app.operations.factory import CalculationFactory
from app.auth.hashing import hash_password


def _make_user(db_session, suffix: str = "calc") -> User:
    user = User(
        username=f"calc_{suffix}",
        email=f"calc_{suffix}@example.com",
        password_hash=hash_password("strongpass1"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_insert_calculation(db_session):
    user = _make_user(db_session, "insert")
    calc_obj = CalculationFactory.create("Multiply", 6, 7)
    calc = Calculation(
        a=6, b=7, type="Multiply",
        result=calc_obj.execute(),
        user_id=user.id,
    )
    db_session.add(calc)
    db_session.commit()
    db_session.refresh(calc)

    fetched = db_session.query(Calculation).filter_by(id=calc.id).one()
    assert fetched.result == 42
    assert fetched.type == "Multiply"
    assert fetched.user_id == user.id
    assert fetched.created_at is not None


def test_user_calculation_relationship(db_session):
    user = _make_user(db_session, "rel")
    for t, a, b in [("Add", 1, 2), ("Sub", 5, 3)]:
        result = CalculationFactory.create(t, a, b).execute()
        db_session.add(Calculation(a=a, b=b, type=t, result=result, user_id=user.id))
    db_session.commit()
    db_session.refresh(user)

    assert len(user.calculations) == 2
    types = {c.type for c in user.calculations}
    assert types == {"Add", "Sub"}


def test_factory_blocks_invalid_type():
    with pytest.raises(ValueError, match="Unknown calculation type"):
        CalculationFactory.create("BogusOp", 2, 3)


def test_factory_blocks_divide_by_zero():
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        CalculationFactory.create("Divide", 5, 0).execute()
