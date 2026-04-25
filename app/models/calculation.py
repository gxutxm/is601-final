"""SQLAlchemy Calculation model."""
from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.db.database import Base


class Calculation(Base):
    """Persisted calculation with a foreign key to the owning user."""

    __tablename__ = "calculations"

    id = Column(Integer, primary_key=True, index=True)
    a = Column(Float, nullable=False)
    b = Column(Float, nullable=False)
    type = Column(String(20), nullable=False)
    result = Column(Float, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="calculations")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Calculation id={self.id} type={self.type} result={self.result}>"
