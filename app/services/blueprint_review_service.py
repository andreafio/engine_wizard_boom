"""
Blueprint Review Service
Creates concise review summaries for user confirmation before generation
"""
from typing import Dict, List, Any
from pydantic import BaseModel, Field
from app.llm.provider import LLMProvider
from app.core.logging import get_logger

logger = get_logger(__name__)


class ReviewSummary(BaseModel):
    """Review summary with categorized blueprint items"""
    confirmed: List[str] = Field(default_factory=list)
    draft_to_confirm: List[str] = Field(default_factory=list)
    missing: List[str] = Field(default_factory=list)


class BlueprintReview(BaseModel):
    """Blueprint review output"""
    review: ReviewSummary


class BlueprintReviewService:
    """
    Service for creating concise review summaries of blueprints for user confirmation.

    Analyzes blueprint completeness and categorizes items as confirmed,
    draft (needs confirmation), or missing. Used before final output generation.
    """

    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider

    async def review_blueprint(self, blueprint: Dict[str, Any]) -> BlueprintReview:
        """
        Create a review summary of the blueprint for user confirmation.

        Args:
            blueprint: Complete blueprint data

        Returns:
            BlueprintReview with categorized items
        """
        logger.info("creating_blueprint_review", sections=list(blueprint.keys()))

        # Build prompt for LLM
        prompt = self._build_review_prompt(blueprint)

        try:
            # Get LLM response
            response = await self.llm.generate_json(
                prompt=prompt,
                system_prompt="You create a concise review summary for user confirmation. No final output generation. Return JSON only."
            )

            # Validate and return
            result = BlueprintReview(**response)

            logger.info(
                "review_created",
                confirmed_count=len(result.review.confirmed),
                draft_count=len(result.review.draft_to_confirm),
                missing_count=len(result.review.missing)
            )

            return result

        except Exception as e:
            logger.error("review_creation_failed", error=str(e))

            # Return safe fallback
            return BlueprintReview(
                review=ReviewSummary(
                    confirmed=["Review generation failed - please verify blueprint manually"],
                    draft_to_confirm=[],
                    missing=[]
                )
            )

    async def build_review(self, blueprint: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build review summary in the format expected by orchestrator.

        Args:
            blueprint: Complete blueprint data

        Returns:
            Review data in orchestrator format
        """
        review_result = await self.review_blueprint(blueprint)
        
        return {
            "confirmed": review_result.review.confirmed,
            "draft_to_confirm": review_result.review.draft_to_confirm,
            "missing": review_result.review.missing
        }

    def _build_review_prompt(self, blueprint: Dict[str, Any]) -> str:
        """Build the review prompt for LLM"""

        # Format blueprint as JSON
        blueprint_json = self._format_blueprint_json(blueprint)

        prompt = f"""SYSTEM:
You create a concise review summary for user confirmation.
No final output generation.

INPUT JSON:
{blueprint_json}

OUTPUT JSON ONLY:
{{
  "review": {{
    "confirmed": ["short bullet", "..."],
    "draft_to_confirm": ["short bullet", "..."],
    "missing": ["short bullet", "..."]
  }}
}}
RULES:
- Keep each bullet short.
- Do not invent missing items.
- Use section names for clarity.

ANALYSIS FRAMEWORK:
- CONFIRMED: Items with complete, confirmed data ready for use
- DRAFT_TO_CONFIRM: Items with draft or incomplete data needing user confirmation
- MISSING: Critical sections or fields that are completely empty

BULLET FORMAT:
- Use section names for clarity (e.g., "Context: industry confirmed")
- Keep each bullet under 50 characters
- Be specific about what's confirmed, draft, or missing
- Focus on key strategic elements

Return JSON only.
"""
        return prompt

    def _format_blueprint_json(self, blueprint: Dict[str, Any]) -> str:
        """Format blueprint as clean JSON string"""
        # Create a clean copy for JSON formatting
        clean_blueprint = {}

        for section, data in blueprint.items():
            if isinstance(data, dict):
                # Remove empty/null values for cleaner JSON
                clean_section = {k: v for k, v in data.items() if v not in (None, '', [], {})}
                if clean_section:
                    clean_blueprint[section] = clean_section
            elif data not in (None, '', [], {}):
                clean_blueprint[section] = data

        return f"""{{
  "blueprint": {clean_blueprint}
}}"""


# Convenience function
async def review_blueprint_for_confirmation(blueprint: Dict[str, Any]) -> BlueprintReview:
    """
    Review a blueprint for user confirmation

    Usage:
        review = await review_blueprint_for_confirmation(blueprint_data)
    """
    from app.llm.openai_provider import OpenAIProvider
    import os

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    llm = OpenAIProvider(api_key=api_key, model="gpt-4o-mini")
    service = BlueprintReviewService(llm)

    return await service.review_blueprint(blueprint)