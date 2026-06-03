"""Lead persistence — save and retrieve completed wizard sessions."""
from datetime import datetime
from typing import Optional
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.db.database import get_session_factory
from app.db.models import Lead
from app.wizard.state import Session
from app.core.logging import get_logger

logger = get_logger(__name__)


def _extract_field(blueprint_section, field: str):
    """Safely extract a field from a BlueprintSection value dict."""
    if blueprint_section and blueprint_section.value and isinstance(blueprint_section.value, dict):
        return blueprint_section.value.get(field)
    return None


async def save_lead(
    session: Session,
    presentation: dict,
    report: dict,
    internal_profile: Optional[dict] = None,
) -> bool:
    """Persist a completed wizard session as a lead. No-op if DB not configured."""
    factory = get_session_factory()
    if factory is None:
        return False

    bp = session.blueprint
    lead = Lead(
        session_id=session.session_id,
        tenant_id=session.tenant_id,
        # Flat queryable fields
        industry=_extract_field(bp.context, "industry"),
        business_model=_extract_field(bp.context, "business_model"),
        company_size=_extract_field(bp.context, "company_size"),
        primary_goal=_extract_field(bp.objective, "primary_goal"),
        target_role=_extract_field(bp.target_market, "target_role"),
        geo_scope=_extract_field(bp.target_market, "geo_scope"),
        offer_type=_extract_field(bp.value_prop, "offer_type"),
        budget_range=_extract_field(bp.constraints, "budget_range"),
        timing=_extract_field(bp.constraints, "timing"),
        channels=_extract_field(bp.channels_assets, "channels"),
        # Full blobs
        blueprint_json=bp.model_dump(),
        presentation_json=presentation,
        report_json=report,
        internal_profile_json=internal_profile,
        created_at=session.created_at,
        completed_at=datetime.utcnow(),
    )

    try:
        async with factory() as db:
            db.add(lead)
            await db.commit()
        logger.info("lead_saved", session_id=session.session_id, tenant_id=session.tenant_id)
        return True
    except IntegrityError:
        # Duplicate session_id — already saved (idempotent re-generate)
        logger.warning("lead_already_exists", session_id=session.session_id)
        return False
    except Exception as e:
        logger.error("lead_save_failed", session_id=session.session_id, error=str(e))
        return False


async def get_lead(session_id: str) -> Optional[Lead]:
    """Retrieve a lead by session_id."""
    factory = get_session_factory()
    if factory is None:
        return None
    try:
        async with factory() as db:
            result = await db.execute(select(Lead).where(Lead.session_id == session_id))
            return result.scalar_one_or_none()
    except Exception as e:
        logger.error("lead_get_failed", session_id=session_id, error=str(e))
        return None
