"""
Field Extractor Service
Strict field extraction from user messages in wizard engine
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from app.llm.provider import LLMProvider
from app.services.clarifier_service import ClarifierService
from app.services.quality_critic_service import QualityCriticService, QualityCritique
from app.core.logging import get_logger

logger = get_logger(__name__)


class ClarifierOptions(BaseModel):
    """Clarifier options for ambiguous answers"""
    ui_type: str  # single_select, multi_select, short_text
    label: str
    options: List[Dict[str, str]] = Field(default_factory=list)


class FieldExtractionResult(BaseModel):
    """Result of field extraction"""
    field: str
    value: Optional[Any] = None
    status: str  # draft, confirmed
    confidence: float  # 0.0 to 1.0
    evidence: str  # max 20 words
    needs_clarification: bool = False
    suggested_clarifier: Optional[ClarifierOptions] = None
    quality_critique: Optional[QualityCritique] = None


class FieldExtractorService:
    """
    Strict field extractor for wizard engine
    
    Extracts values from user messages for specific fields.
    Never invents facts, numbers, KPIs, budgets, targets.
    Returns draft status with clarifier if ambiguous.
    """

    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider
        self.clarifier = ClarifierService(llm_provider)
        self.quality_critic = QualityCriticService(llm_provider)

    async def extract_field(
        self,
        current_section: str,
        current_field: str,
        ui_type: str,
        options: List[Dict[str, str]],
        user_message: str,
        blueprint_snippet: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> FieldExtractionResult:
        """
        Extract field value from user message
        
        Args:
            current_section: Context|Objective|Offer|Audience|Funnel|Channels|AssetsTracking|Constraints|Risks
            current_field: dot.notation.field
            ui_type: single_select|multi_select|short_text|long_text
            options: [{"id": "", "label": ""}]
            user_message: user's free text answer
            blueprint_snippet: current field state
            
        Returns:
            FieldExtractionResult with extracted value
        """
        logger.info(
            "extracting_field",
            field=current_field,
            ui_type=ui_type,
            message_length=len(user_message)
        )

        # Check for uncertainty expressions
        uncertainty_keywords = ["non so", "boh", "non sono sicuro", "forse", "circa", "più o meno"]
        has_uncertainty = any(keyword in user_message.lower() for keyword in uncertainty_keywords)

        # Prepare LLM prompt
        prompt = self._build_extraction_prompt(
            current_section=current_section,
            current_field=current_field,
            ui_type=ui_type,
            options=options,
            user_message=user_message,
            blueprint_snippet=blueprint_snippet,
            has_uncertainty=has_uncertainty
        )

        try:
            # Get LLM response
            response = await self.llm.generate_json(
                prompt=prompt,
                system_prompt="You are a strict field extractor. Extract ONLY the specified field value. Never invent facts or numbers. Return valid JSON only."
            )

            # Parse and validate response
            result = FieldExtractionResult(**response)

            # Adjust confidence if uncertainty detected
            if has_uncertainty and result.confidence > 0.5:
                result.confidence = 0.4
                result.evidence += " (user expressed uncertainty)"

            # Generate clarifier options if needed
            if result.needs_clarification and not result.suggested_clarifier:
                try:
                    # Use provided context or extract from blueprint_snippet
                    clarifier_context = context or {}
                    if not clarifier_context and blueprint_snippet:
                        # Extract basic context from blueprint if available
                        # This could be enhanced to extract more context from session
                        pass

                    result.suggested_clarifier = await self.clarifier.generate_clarifier(
                        current_field=current_field,
                        context=clarifier_context,
                        user_message=user_message
                    )
                except Exception as ce:
                    logger.warning("clarifier_generation_failed", field=current_field, error=str(ce))
                    # Keep the result as is, clarifier will be None

            # Critique answer quality if value was extracted
            if result.value is not None and result.confidence > 0.3:
                try:
                    result.quality_critique = await self.quality_critic.critique_answer(
                        field=current_field,
                        value=result.value,
                        ui_type=ui_type,
                        section=current_section
                    )
                except Exception as qe:
                    logger.warning("quality_critique_failed", field=current_field, error=str(qe))
                    # Keep result as is, critique will be None

            logger.info(
                "field_extracted",
                field=current_field,
                status=result.status,
                confidence=result.confidence,
                needs_clarification=result.needs_clarification,
                quality_score=result.quality_critique.quality_score if result.quality_critique else None
            )

            return result

        except Exception as e:
            logger.error("field_extraction_failed", field=current_field, error=str(e))

            # Return safe fallback
            return FieldExtractionResult(
                field=current_field,
                value=None,
                status="draft",
                confidence=0.0,
                evidence="extraction failed",
                needs_clarification=True,
                suggested_clarifier=ClarifierOptions(
                    ui_type="short_text",
                    label=f"Per favore, fornisci più dettagli su {current_field.replace('.', ' ')}"
                ),
                quality_critique=None
            )

    def _build_extraction_prompt(
        self,
        current_section: str,
        current_field: str,
        ui_type: str,
        options: List[Dict[str, str]],
        user_message: str,
        blueprint_snippet: Dict[str, Any],
        has_uncertainty: bool
    ) -> str:
        """Build the extraction prompt for LLM"""

        # Format options for prompt
        options_text = ""
        if options:
            options_text = "\n".join([f"- {opt['id']}: {opt['label']}" for opt in options])

        # Current field state
        field_state = blueprint_snippet.get("field_state", {})
        current_status = field_state.get("status", "missing")
        current_value = field_state.get("value")

        prompt = f"""
You are a strict field extractor inside a wizard engine.
You do not chat. You only extract structured data.

CONTEXT:
- Current section: {current_section}
- Current field: {current_field}
- UI type: {ui_type}
- Current field status: {current_status}
- Current field value: {current_value}

AVAILABLE OPTIONS:
{options_text}

USER MESSAGE:
"{user_message}"

TASK:
Extract ONLY the value for {current_field} from the user message.
- If UI type is single_select/multi_select, map to option IDs when possible
- If answer is ambiguous, return draft status + suggested_clarifier
- Never invent facts, numbers, KPIs, budgets, targets
- If user expresses uncertainty, set low confidence (0.0-0.4)

OUTPUT JSON ONLY:
{{
  "field": "{current_field}",
  "value": null,
  "status": "draft|confirmed",
  "confidence": 0.0,
  "evidence": "max 20 words, short quote or rationale",
  "needs_clarification": false,
  "suggested_clarifier": {{
    "ui_type": "single_select|multi_select|short_text",
    "label": "string",
    "options": [{{"id":"", "label":""}}]
  }}
}}

RULES:
- Only fill {current_field}. Do not output other fields.
- Keep output strictly valid JSON. No markdown.
- If no clear value found, set status="draft" and needs_clarification=true
"""

        return prompt


# Convenience function
async def extract_wizard_field(
    current_section: str,
    current_field: str,
    ui_type: str,
    options: List[Dict[str, str]],
    user_message: str,
    blueprint_snippet: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None
) -> FieldExtractionResult:
    """
    Extract field value from wizard user input
    
    Usage:
        result = await extract_wizard_field(
            current_section="Context",
            current_field="context.industry",
            ui_type="single_select",
            options=[{"id": "b2b", "label": "B2B"}],
            user_message="Siamo una azienda B2B",
            blueprint_snippet={"field_state": {"value": null, "status": "missing"}}
        )
    """
    from app.llm.openai_provider import OpenAIProvider
    import os

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    llm = OpenAIProvider(api_key=api_key, model="gpt-4o-mini")
    service = FieldExtractorService(llm)

    return await service.extract_field(
        current_section=current_section,
        current_field=current_field,
        ui_type=ui_type,
        options=options,
        user_message=user_message,
        blueprint_snippet=blueprint_snippet,
        context=context
    )
