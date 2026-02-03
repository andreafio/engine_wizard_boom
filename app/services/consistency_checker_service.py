"""
Consistency Checker Service
Detects logical inconsistencies across related blueprint fields
"""
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from app.core.logging import get_logger

logger = get_logger(__name__)


class Conflict(BaseModel):
    """A detected conflict"""
    description: str
    affected_fields: List[str]


class ConsistencyCheckResult(BaseModel):
    """Result of consistency check"""
    has_conflicts: bool
    conflicts: List[Conflict]


class ConsistencyCheckerService:
    """
    Service for checking consistency across related blueprint fields.
    Detects logical inconsistencies or contradictions without resolving them.
    """

    def check_consistency(
        self,
        blueprint_section: str,
        fields: Dict[str, Any]
    ) -> ConsistencyCheckResult:
        """
        Check for consistency across fields in a blueprint section.

        Args:
            blueprint_section: The blueprint section (Offer, Audience, Funnel, Channels)
            fields: Dict of field names to values

        Returns:
            ConsistencyCheckResult with conflicts if any
        """
        conflicts = []

        # Section-specific consistency checks
        if blueprint_section == "Offer":
            conflicts.extend(self._check_offer_consistency(fields))
        elif blueprint_section == "Audience":
            conflicts.extend(self._check_audience_consistency(fields))
        elif blueprint_section == "Funnel":
            conflicts.extend(self._check_funnel_consistency(fields))
        elif blueprint_section == "Channels":
            conflicts.extend(self._check_channels_consistency(fields))

        return ConsistencyCheckResult(
            has_conflicts=len(conflicts) > 0,
            conflicts=conflicts
        )

    def _check_offer_consistency(self, fields: Dict[str, Any]) -> List[Conflict]:
        """Check consistency in Offer section"""
        conflicts = []

        # Example: If ticket_range is "enterprise" but type is "consumer product"
        ticket_range = fields.get("ticket_range", "").lower()
        offer_type = fields.get("type", "").lower()

        if "enterprise" in ticket_range and "consumer" in offer_type:
            conflicts.append(Conflict(
                description="Enterprise ticket range conflicts with consumer offer type",
                affected_fields=["ticket_range", "type"]
            ))

        return conflicts

    def _check_audience_consistency(self, fields: Dict[str, Any]) -> List[Conflict]:
        """Check consistency in Audience section"""
        conflicts = []

        # Example: If target_role is "CTO" but main_pain is "affordable pricing"
        target_role = fields.get("target_role", "").lower()
        main_pain = fields.get("main_pain", "").lower()

        if "cto" in target_role and "affordable" in main_pain:
            conflicts.append(Conflict(
                description="CTO role unlikely to have affordable pricing as main pain",
                affected_fields=["target_role", "main_pain"]
            ))

        return conflicts

    def _check_funnel_consistency(self, fields: Dict[str, Any]) -> List[Conflict]:
        """Check consistency in Funnel section"""
        conflicts = []

        # Example: If primary_cta is "download free trial" but lead_magnet is "paid consultation"
        primary_cta = fields.get("primary_cta", "").lower()
        lead_magnet = fields.get("lead_magnet", "").lower()

        if "free" in primary_cta and "paid" in lead_magnet:
            conflicts.append(Conflict(
                description="Free CTA conflicts with paid lead magnet",
                affected_fields=["primary_cta", "lead_magnet"]
            ))

        return conflicts

    def _check_channels_consistency(self, fields: Dict[str, Any]) -> List[Conflict]:
        """Check consistency in Channels section"""
        conflicts = []

        # Example: If primary_channel is "linkedin" but target_audience is "consumers under 18"
        primary_channel = fields.get("primary_channel", "").lower()
        target_audience = fields.get("target_audience", "").lower()

        if "linkedin" in primary_channel and "under 18" in target_audience:
            conflicts.append(Conflict(
                description="LinkedIn not suitable for audience under 18",
                affected_fields=["primary_channel", "target_audience"]
            ))

        return conflicts