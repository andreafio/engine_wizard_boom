"""
Clarifier Service
Generates clarifying options for wizard UI when field extraction is ambiguous
"""
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from app.llm.provider import LLMProvider
from app.core.logging import get_logger

logger = get_logger(__name__)


class ClarifierOptions(BaseModel):
    """Clarifier options for UI"""
    ui_type: str = "single_select"
    label: str
    options: List[Dict[str, str]] = Field(min_length=3, max_length=6)


class ClarifierService:
    """
    Service for generating clarifying options when field extraction is ambiguous.

    Generates 3-6 plausible, generic options relevant to the context without
    inventing facts, numbers, or performance claims.
    """

    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider

    async def generate_clarifier(
        self,
        current_field: str,
        context: Dict[str, Any],
        user_message: str
    ) -> ClarifierOptions:
        """
        Generate clarifying options for ambiguous field extraction.

        Args:
            current_field: Dot notation field path (e.g., "context.industry")
            context: Optional context with industry, business_model, etc.
            user_message: Original user message that was ambiguous

        Returns:
            ClarifierOptions with 3-6 relevant options
        """
        logger.info(
            "generating_clarifier",
            field=current_field,
            context_keys=list(context.keys()),
            message_length=len(user_message)
        )

        # Build prompt for LLM
        prompt = self._build_clarifier_prompt(current_field, context, user_message)

        try:
            # Get LLM response
            response = await self.llm.generate_json(
                prompt=prompt,
                system_prompt="You generate clarifying options for a wizard UI. You do not invent facts; you propose plausible choices. Output valid JSON only."
            )

            # Validate and return
            result = ClarifierOptions(**response)

            logger.info(
                "clarifier_generated",
                field=current_field,
                option_count=len(result.options)
            )

            return result

        except Exception as e:
            logger.error("clarifier_generation_failed", field=current_field, error=str(e))

            # Return safe fallback based on field type
            return self._get_fallback_clarifier(current_field)

    def _build_clarifier_prompt(
        self,
        current_field: str,
        context: Dict[str, Any],
        user_message: str
    ) -> str:
        """Build the clarifier prompt for LLM"""

        # Extract field category from dot notation
        field_parts = current_field.split('.')
        field_category = field_parts[0] if field_parts else "general"
        field_name = field_parts[-1] if field_parts else current_field

        # Format context
        context_str = ""
        if context:
            context_items = []
            for key, value in context.items():
                if value and value != "optional":
                    context_items.append(f"{key}: {value}")
            if context_items:
                context_str = f"Context: {', '.join(context_items)}\n"

        prompt = f"""You generate clarifying options for a wizard UI.
You do not invent facts; you propose plausible choices.

CURRENT FIELD: {current_field}
{context_str}
USER MESSAGE: "{user_message}"

TASK:
Propose 3–6 concise options the user can select to clarify the field.
Options must be generic but relevant to the context.
Do NOT include numbers, KPIs, or performance claims.

OUTPUT JSON ONLY:
{{
  "ui_type": "single_select",
  "label": "string",
  "options": [
    {{"id": "option1", "label": "Option 1"}},
    {{"id": "option2", "label": "Option 2"}},
    {{"id": "option3", "label": "Option 3"}}
  ]
}}

GUIDELINES:
- Label should be a clear question asking for clarification
- Options should be mutually exclusive and cover common scenarios
- Keep options generic and business-appropriate
- Use descriptive but concise labels
- IDs should be simple, lowercase identifiers
"""

        return prompt

    def _get_fallback_clarifier(self, current_field: str) -> ClarifierOptions:
        """Get fallback clarifier when LLM fails"""

        field_name = current_field.split('.')[-1]

        # Generic fallbacks based on common field types
        fallbacks = {
            "industry": ClarifierOptions(
                ui_type="single_select",
                label=f"Qual è il tuo settore di attività principale?",
                options=[
                    {"id": "tech", "label": "Tecnologia"},
                    {"id": "finance", "label": "Finanza"},
                    {"id": "healthcare", "label": "Sanità"},
                    {"id": "retail", "label": "Commercio"},
                    {"id": "manufacturing", "label": "Produzione"}
                ]
            ),
            "business_model": ClarifierOptions(
                ui_type="single_select",
                label=f"Qual è il tuo modello di business?",
                options=[
                    {"id": "b2b", "label": "B2B (Business to Business)"},
                    {"id": "b2c", "label": "B2C (Business to Consumer)"},
                    {"id": "b2b2c", "label": "B2B2C (piattaforme)"},
                    {"id": "marketplace", "label": "Marketplace"},
                    {"id": "subscription", "label": "Abbonamento/SaaS"}
                ]
            ),
            "target_audience": ClarifierOptions(
                ui_type="single_select",
                label=f"Qual è il tuo pubblico target principale?",
                options=[
                    {"id": "individuals", "label": "Privati/Consumatori"},
                    {"id": "small_business", "label": "Piccole imprese"},
                    {"id": "enterprises", "label": "Grandi aziende"},
                    {"id": "professionals", "label": "Professionisti"},
                    {"id": "general_public", "label": "Pubblico generico"}
                ]
            )
        }

        # Return specific fallback or generic one
        return fallbacks.get(field_name, ClarifierOptions(
            ui_type="single_select",
            label=f"Per favore, specifica meglio {field_name.replace('_', ' ')}",
            options=[
                {"id": "option1", "label": "Prima opzione"},
                {"id": "option2", "label": "Seconda opzione"},
                {"id": "option3", "label": "Terza opzione"}
            ]
        ))


# Convenience function
async def generate_field_clarifier(
    current_field: str,
    context: Dict[str, Any],
    user_message: str
) -> ClarifierOptions:
    """
    Generate clarifying options for a field

    Usage:
        clarifier = await generate_field_clarifier(
            current_field="context.industry",
            context={"business_model": "b2b"},
            user_message="Siamo nel tech"
        )
    """
    from app.llm.openai_provider import OpenAIProvider
    import os

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    llm = OpenAIProvider(api_key=api_key, model="gpt-4o-mini")
    service = ClarifierService(llm)

    return await service.generate_clarifier(current_field, context, user_message)
