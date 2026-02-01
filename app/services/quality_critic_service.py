"""
Quality Critic Service
Scores the quality of wizard answers and recommends follow-ups
"""
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from app.llm.provider import LLMProvider
from app.core.logging import get_logger

logger = get_logger(__name__)


class QualityCritique(BaseModel):
    """Quality critique result"""
    quality_score: float = Field(ge=0.0, le=1.0)
    is_vague: bool
    recommend_deep: bool
    recommended_followup_field: Optional[str] = None
    reason: str = Field(max_length=50)


class QualityCriticService:
    """
    Service for scoring answer quality and recommending follow-ups.

    Uses rule-based scoring to evaluate wizard answers for completeness,
    specificity, and actionability. Recommends follow-up fields when
    answers are vague or insufficient.
    """

    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        self.llm = llm_provider  # Kept for backward compatibility, but not used

    async def critique_answer(
        self,
        field: str,
        value: Any,
        ui_type: str,
        section: str
    ) -> QualityCritique:
        """
        Critique the quality of a wizard answer using rule-based scoring.

        Args:
            field: Dot notation field path (e.g., "context.industry")
            value: The answer value (string or structured)
            ui_type: UI component type (short_text, long_text, single_select, multi_select)
            section: Wizard section (Context, Objective, etc.)

        Returns:
            QualityCritique with score and recommendations
        """
        logger.info(
            "critiquing_answer",
            field=field,
            ui_type=ui_type,
            section=section,
            value_type=type(value).__name__
        )

        try:
            # Rule-based quality scoring
            result = self._rule_based_critique(field, value, ui_type, section)

            logger.info(
                "answer_critiqued",
                field=field,
                score=result.quality_score,
                is_vague=result.is_vague,
                recommend_deep=result.recommend_deep
            )

            return result

        except Exception as e:
            logger.error("critique_failed", field=field, error=str(e))

            # Return safe fallback
            return QualityCritique(
                quality_score=0.5,
                is_vague=False,
                recommend_deep=False,
                recommended_followup_field=None,
                reason="critique failed"
            )

    def _rule_based_critique(
        self,
        field: str,
        value: Any,
        ui_type: str,
        section: str
    ) -> QualityCritique:
        """
        Rule-based quality critique implementation.
        """
        # Handle empty/null values
        if value is None or value == "" or (isinstance(value, list) and len(value) == 0):
            return QualityCritique(
                quality_score=0.0,
                is_vague=True,
                recommend_deep=True,
                recommended_followup_field=self._get_followup_field(section, field),
                reason="empty value"
            )

        # Convert value to string for analysis
        if isinstance(value, list):
            value_str = " ".join(str(v) for v in value)
        else:
            value_str = str(value)

        # Get field name for specific logic
        field_name = field.split('.')[-1]

        # Score based on UI type and content
        if ui_type in ["single_select", "multi_select"]:
            # Select fields are usually good if they have values
            score = 0.9 if value else 0.0
            is_vague = False
            reason = "selection made"

        elif ui_type in ["short_text", "long_text"]:
            score, is_vague, reason = self._score_text_answer(value_str, field_name, ui_type)

        else:
            # Unknown UI type
            score = 0.5
            is_vague = False
            reason = "unknown ui type"

        # Determine if deep follow-up is needed
        recommend_deep = score < 0.5 and is_vague
        followup_field = self._get_followup_field(section, field) if recommend_deep else None

        return QualityCritique(
            quality_score=round(score, 2),
            is_vague=is_vague,
            recommend_deep=recommend_deep,
            recommended_followup_field=followup_field,
            reason=reason
        )

    def _score_text_answer(self, value_str: str, field_name: str, ui_type: str) -> tuple[float, bool, str]:
        """
        Score text answers for specificity and actionability.
        Returns (score, is_vague, reason)
        """
        # Clean the text
        text = value_str.strip().lower()

        # Check for generic marketing phrases (strict scoring)
        generic_phrases = [
            "grow my business", "increase sales", "build brand awareness",
            "reach more customers", "improve marketing", "digital marketing",
            "social media marketing", "content marketing", "marketing strategy",
            "business development", "customer acquisition", "lead generation",
            "brand building", "market expansion", "revenue growth"
        ]

        if any(phrase in text for phrase in generic_phrases):
            return 0.2, True, "generic marketing phrase"

        # Check length requirements
        word_count = len(text.split())

        if ui_type == "short_text":
            if word_count < 3:
                return 0.3, True, "too brief"
            elif word_count > 50:
                return 0.4, False, "too verbose for short text"
            else:
                # Check for specificity
                if self._has_specific_details(text, field_name):
                    return 0.8, False, "specific and concise"
                else:
                    return 0.5, True, "lacks specificity"

        elif ui_type == "long_text":
            if word_count < 10:
                return 0.2, True, "insufficient detail"
            elif word_count < 20:
                return 0.4, True, "needs more detail"
            else:
                # Check for specificity and actionability
                if self._has_specific_details(text, field_name):
                    return 0.9, False, "detailed and specific"
                else:
                    return 0.6, True, "generic content"

        return 0.5, False, "acceptable"

    def _has_specific_details(self, text: str, field_name: str) -> bool:
        """
        Check if text contains specific, actionable details.
        """
        # Normalize field name (remove suffixes like _range)
        base_field_name = field_name.split('_')[0] if '_' in field_name else field_name

        # Field-specific specificity checks
        specificity_indicators = {
            "industry": ["technology", "healthcare", "finance", "retail", "manufacturing", "software", "consulting", "e-commerce", "saas", "platform"],
            "description": ["products", "services", "customers", "market", "solution", "platform", "company", "business"],
            "goal": ["increase", "achieve", "target", "grow", "by", "%", "$", "€", "revenue", "customers", "users"],
            "budget": ["$", "€", "£", "budget", "investment", "cost", "spend", "amount", "range", "quarter", "month", "year"],
            "timeline": ["month", "quarter", "year", "week", "202", "deadline", "by", "within", "target date"],
            "audience": ["customers", "users", "clients", "businesses", "individuals", "age", "role", "segment", "demographics"],
            "value_prop": ["helps", "enables", "provides", "allows", "solves", "improves", "reduces", "automates"],
            "pricing": ["$", "€", "£", "month", "year", "subscription", "package", "fee", "cost"],
            "features": ["includes", "has", "offers", "provides", "supports", "integrates"],
            "differentiator": ["unique", "different", "better", "faster", "cheaper", "easier", "automated", "ai", "machine learning"]
        }

        indicators = specificity_indicators.get(base_field_name, ["specific", "details", "particular", "concrete"])
        return any(indicator in text for indicator in indicators)

    def _get_followup_field(self, section: str, current_field: str) -> Optional[str]:
        """
        Get a deep follow-up field from the same section.
        """
        field_name = current_field.split('.')[-1]

        # Section-specific follow-up mappings
        followups = {
            "Context": {
                "industry": "context.company_size",
                "company_name": "context.industry",
                "website_url": "context.business_model",
                "business_model": "context.company_size"
            },
            "Objective": {
                "primary_goal": "objective.secondary_goals",
                "secondary_goals": "objective.success_definition",
                "success_definition": "objective.time_horizon",
                "time_horizon": "objective.success_definition"
            },
            "Offer": {
                "type": "offer.one_liner",
                "one_liner": "offer.ticket_range",
                "ticket_range": "offer.sales_cycle",
                "sales_cycle": "offer.differentiator"
            },
            "Audience": {
                "target_role": "audience.main_pain",
                "main_pain": "audience.trigger",
                "trigger": "audience.main_objection",
                "main_objection": "audience.decision_process"
            },
            "Funnel": {
                "primary_cta": "funnel.lead_magnet",
                "lead_magnet": "funnel.conversion_path",
                "conversion_path": "funnel.sales_handoff",
                "sales_handoff": "funnel.primary_cta"
            },
            "Channels": {
                "current": "channels.recommended",
                "recommended": "channels.priority",
                "priority": "channels.notes",
                "notes": "channels.current"
            },
            "AssetsTracking": {
                "has_landing": "assets_tracking.assets_ready",
                "assets_ready": "assets_tracking.tracking_stack",
                "tracking_stack": "assets_tracking.crm",
                "crm": "assets_tracking.analytics_access"
            },
            "Constraints": {
                "budget_range": "constraints.timing",
                "timing": "constraints.internal_resources",
                "internal_resources": "constraints.notes",
                "notes": "constraints.budget_range"
            },
            "Risks": {
                "main_risk": "risks.unknowns",
                "unknowns": "risks.main_risk"
            }
        }

        return followups.get(section, {}).get(field_name)


# Convenience function
async def critique_wizard_answer(
    field: str,
    value: Any,
    ui_type: str,
    section: str
) -> QualityCritique:
    """
    Critique a wizard answer for quality

    Usage:
        critique = await critique_wizard_answer(
            field="context.industry",
            value="Technology",
            ui_type="single_select",
            section="Context"
        )
    """
    from app.llm.openai_provider import OpenAIProvider
    import os

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    llm = OpenAIProvider(api_key=api_key, model="gpt-4o-mini")
    service = QualityCriticService(llm)

    return await service.critique_answer(field, value, ui_type, section)
