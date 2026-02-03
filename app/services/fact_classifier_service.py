"""
Fact Classifier Service
Classifies statements as facts or assumptions based on field status
"""
from typing import Dict, Any
from pydantic import BaseModel, Field
from app.core.logging import get_logger

logger = get_logger(__name__)


class FactClassification(BaseModel):
    """Classification result"""
    classification: str = Field(regex="^(fact|assumption)$")
    reason: str = Field(max_length=50)


class FactClassifierService:
    """
    Service for classifying statements as facts or assumptions.
    Based on the source field status.
    """

    def classify_statement(
        self,
        statement: str,
        source_field_status: str
    ) -> FactClassification:
        """
        Classify a statement as fact or assumption.

        Args:
            statement: The statement to classify
            source_field_status: Status of the source field (confirmed|draft|missing)

        Returns:
            FactClassification
        """
        if source_field_status == "confirmed":
            return FactClassification(
                classification="fact",
                reason="confirmed field"
            )
        elif source_field_status in ["draft", "missing"]:
            return FactClassification(
                classification="assumption",
                reason="draft or missing field"
            )
        else:
            # Unknown status, treat as assumption
            return FactClassification(
                classification="assumption",
                reason="unknown field status"
            )