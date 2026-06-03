"""SQLAlchemy ORM models."""
import uuid
from datetime import datetime
from sqlalchemy import DateTime, String, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base


class Lead(Base):
    """A completed wizard session with its generated profile."""
    __tablename__ = "leads"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    tenant_id: Mapped[str] = mapped_column(String, index=True)

    # Flat fields for easy filtering/querying
    industry: Mapped[str | None] = mapped_column(String, nullable=True)
    business_model: Mapped[str | None] = mapped_column(String, nullable=True)
    company_size: Mapped[str | None] = mapped_column(String, nullable=True)
    primary_goal: Mapped[str | None] = mapped_column(String, nullable=True)
    target_role: Mapped[str | None] = mapped_column(String, nullable=True)
    geo_scope: Mapped[str | None] = mapped_column(String, nullable=True)
    offer_type: Mapped[str | None] = mapped_column(String, nullable=True)
    budget_range: Mapped[str | None] = mapped_column(String, nullable=True)
    timing: Mapped[str | None] = mapped_column(String, nullable=True)
    channels: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Full JSON blobs
    blueprint_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    presentation_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    report_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    internal_profile_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
