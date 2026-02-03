"""
Integrity Summarizer Service
Summarizes data integrity for transparency
"""
from typing import Dict, Any
from pydantic import BaseModel, Field
from app.core.logging import get_logger

logger = get_logger(__name__)


class IntegritySummary(BaseModel):
    """Integrity summary result"""
    integrity_level: str = Field(regex="^(high|medium|low)$")
    message: str


class IntegritySummarizerService:
    """
    Service for summarizing data integrity levels.
    Provides transparency without judgments.
    """

    def summarize_integrity(
        self,
        blueprint: Dict[str, Any]
    ) -> IntegritySummary:
        """
        Summarize the integrity level of a blueprint.

        Args:
            blueprint: Dict with confirmed_count, draft_count, missing_count

        Returns:
            IntegritySummary
        """
        confirmed = blueprint.get("confirmed_count", 0)
        draft = blueprint.get("draft_count", 0)
        missing = blueprint.get("missing_count", 0)

        total = confirmed + draft + missing

        if total == 0:
            return IntegritySummary(
                integrity_level="high",
                message="No fields to evaluate"
            )

        confirmed_ratio = confirmed / total
        incomplete_ratio = (draft + missing) / total

        if confirmed_ratio >= 0.8:
            level = "high"
            message = f"{confirmed} of {total} fields confirmed"
        elif incomplete_ratio >= 0.5:
            level = "low"
            message = f"{draft + missing} of {total} fields incomplete"
        else:
            level = "medium"
            message = f"Mixed status: {confirmed} confirmed, {draft} draft, {missing} missing"

        return IntegritySummary(
            integrity_level=level,
            message=message
        )