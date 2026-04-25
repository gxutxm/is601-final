"""Calculation routes: BREAD operations + stats, scoped to the authenticated user."""
from collections import Counter
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.jwt import get_current_user
from app.db.database import get_db
from app.models.calculation import Calculation
from app.models.user import User
from app.operations.factory import CalculationFactory
from app.schemas.calculation import (
    CalculationCreate,
    CalculationRead,
    CalculationStats,
    CalculationUpdate,
)

router = APIRouter(prefix="/calculations", tags=["calculations"])


def _compute(calc_type: str, a: float, b: float) -> float:
    """Delegate arithmetic to the Factory so the same logic drives all routes."""
    return CalculationFactory.create(calc_type, a, b).execute()


def _owned_or_404(
    calc_id: int, db: Session, current_user: User
) -> Calculation:
    """Fetch a calculation owned by the current user, else 404."""
    calc = db.query(Calculation).filter(Calculation.id == calc_id).first()
    if calc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Calculation not found")
    if calc.user_id != current_user.id:
        # 404 (not 403) hides the existence of other users' records.
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Calculation not found")
    return calc


# ---------- Add ----------
@router.post(
    "",
    response_model=CalculationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new calculation",
)
def create_calculation(
    payload: CalculationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Calculation:
    try:
        result = _compute(payload.type, payload.a, payload.b)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))

    calc = Calculation(
        a=payload.a,
        b=payload.b,
        type=payload.type,
        result=result,
        user_id=current_user.id,
    )
    db.add(calc)
    db.commit()
    db.refresh(calc)
    return calc


# ---------- Browse ----------
@router.get(
    "",
    response_model=List[CalculationRead],
    summary="List all calculations owned by the current user",
)
def list_calculations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[Calculation]:
    return (
        db.query(Calculation)
        .filter(Calculation.user_id == current_user.id)
        .order_by(Calculation.id.desc())
        .all()
    )


# ---------- Stats (NEW: final project) ----------
# IMPORTANT: This route must be declared before /{calc_id} so FastAPI
# doesn't try to match "stats" as the calc_id path parameter.
@router.get(
    "/stats",
    response_model=CalculationStats,
    summary="Aggregate stats over the current user's calculations",
)
def calculation_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CalculationStats:
    """Return total counts, per-type breakdown, and operand/result averages.

    All aggregation is scoped to the calling user — there's no way to peek
    at anyone else's stats.
    """
    base = db.query(Calculation).filter(Calculation.user_id == current_user.id)
    total = base.count()

    if total == 0:
        return CalculationStats(
            total=0,
            by_type={},
            most_used_type=None,
            avg_a=None,
            avg_b=None,
            avg_result=None,
        )

    # Per-type counts via a single GROUP BY query — no Python loop.
    type_counts = dict(
        db.query(Calculation.type, func.count(Calculation.id))
        .filter(Calculation.user_id == current_user.id)
        .group_by(Calculation.type)
        .all()
    )
    most_used = Counter(type_counts).most_common(1)[0][0]

    # Numeric averages — let Postgres do the math.
    avg_a, avg_b, avg_result = (
        db.query(
            func.avg(Calculation.a),
            func.avg(Calculation.b),
            func.avg(Calculation.result),
        )
        .filter(Calculation.user_id == current_user.id)
        .one()
    )

    return CalculationStats(
        total=total,
        by_type=type_counts,
        most_used_type=most_used,
        avg_a=float(avg_a) if avg_a is not None else None,
        avg_b=float(avg_b) if avg_b is not None else None,
        avg_result=float(avg_result) if avg_result is not None else None,
    )


# ---------- Read ----------
@router.get(
    "/{calc_id}",
    response_model=CalculationRead,
    summary="Retrieve a single calculation by id",
)
def get_calculation(
    calc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Calculation:
    return _owned_or_404(calc_id, db, current_user)


# ---------- Edit ----------
@router.put(
    "/{calc_id}",
    response_model=CalculationRead,
    summary="Update a calculation (recomputes the result)",
)
def update_calculation(
    calc_id: int,
    payload: CalculationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Calculation:
    calc = _owned_or_404(calc_id, db, current_user)

    if payload.a is not None:
        calc.a = payload.a
    if payload.b is not None:
        calc.b = payload.b
    if payload.type is not None:
        calc.type = payload.type

    try:
        calc.result = _compute(calc.type, calc.a, calc.b)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))

    db.commit()
    db.refresh(calc)
    return calc


# ---------- Delete ----------
@router.delete(
    "/{calc_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Permanently delete a calculation",
)
def delete_calculation(
    calc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    calc = _owned_or_404(calc_id, db, current_user)
    db.delete(calc)
    db.commit()
    return None
