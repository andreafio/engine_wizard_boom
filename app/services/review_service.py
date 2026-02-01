"""Review service for blueprint validation before generation."""
from typing import Dict, Any
from pydantic import ValidationError
from app.llm.provider import LLMProvider
from app.llm.prompts import build_review_prompt, REVIEWER_SYSTEM_PROMPT
from app.services.review_schema import ReviewOutput
from app.wizard.state import Session
from app.core.logging import get_logger

logger = get_logger(__name__)


class ReviewService:
    """Service for reviewing blueprint before generation."""
    
    def __init__(self, llm_provider: LLMProvider):
        """Initialize review service.
        
        Args:
            llm_provider: LLM provider instance
        """
        self.llm = llm_provider
    
    async def review_blueprint(self, session: Session) -> Dict[str, Any]:
        """Generate review summary of blueprint for user confirmation.
        
        This is called before final generation to show user what will be
        included in the output and what needs confirmation.
        
        Args:
            session: Session with blueprint to review
            
        Returns:
            Review output with confirmed and to_confirm lists
        """
        logger.info("review_started", session_id=session.session_id)
        
        # Build blueprint dict with status information
        blueprint_dict = {
            "context": {
                "value": session.blueprint.context.value if session.blueprint.context.value else {},
                "status": session.blueprint.context.status.value if session.blueprint.context.status else "draft"
            },
            "objective": {
                "value": session.blueprint.objective.value if session.blueprint.objective.value else {},
                "status": session.blueprint.objective.status.value if session.blueprint.objective.status else "draft"
            },
            "target_market": {
                "value": session.blueprint.target_market.value if session.blueprint.target_market.value else {},
                "status": session.blueprint.target_market.status.value if session.blueprint.target_market.status else "draft"
            },
            "value_prop": {
                "value": session.blueprint.value_prop.value if session.blueprint.value_prop.value else {},
                "status": session.blueprint.value_prop.status.value if session.blueprint.value_prop.status else "draft"
            },
            "channels_assets": {
                "value": session.blueprint.channels_assets.value if session.blueprint.channels_assets.value else {},
                "status": session.blueprint.channels_assets.status.value if session.blueprint.channels_assets.status else "draft"
            },
            "constraints": {
                "value": session.blueprint.constraints.value if session.blueprint.constraints.value else {},
                "status": session.blueprint.constraints.status.value if session.blueprint.constraints.status else "draft"
            }
        }
        
        # Generate review using LLM
        try:
            prompt = build_review_prompt(blueprint_dict)
            result = await self.llm.generate_json(
                prompt=prompt,
                system_prompt=REVIEWER_SYSTEM_PROMPT
            )
            
            # Validate with Pydantic schema
            try:
                validated_output = ReviewOutput.model_validate(result)
                result = validated_output.model_dump()
                
                logger.info("review_completed",
                           session_id=session.session_id,
                           confirmed_count=len(validated_output.review.confirmed),
                           to_confirm_count=len(validated_output.review.to_confirm),
                           ready_for_generation=validated_output.is_ready_for_generation())
                
            except ValidationError as ve:
                logger.warning("review_validation_failed",
                             session_id=session.session_id,
                             errors=ve.errors())
                # Continue with unvalidated result as fallback
            
            return result
            
        except Exception as e:
            logger.error("review_failed", session_id=session.session_id, error=str(e))
            
            # Return fallback review
            return self._get_fallback_review(blueprint_dict)
    
    def _get_fallback_review(self, blueprint_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback review when LLM fails.
        
        Args:
            blueprint_dict: Blueprint data with status
            
        Returns:
            Fallback review structure
        """
        confirmed = []
        to_confirm = []
        
        # Manually extract items by status
        for section_name, section_data in blueprint_dict.items():
            if not section_data or not isinstance(section_data, dict):
                continue
            
            value = section_data.get('value', {})
            status = section_data.get('status', 'draft')
            
            if not value or (isinstance(value, dict) and not value):
                continue
            
            # Format section for display
            section_label = section_name.replace('_', ' ').title()
            
            if isinstance(value, dict):
                for k, v in value.items():
                    if v not in (None, '', [], {}):
                        item = f"{section_label} - {k}: {v}"
                        if status == "confirmed":
                            confirmed.append(item)
                        else:
                            to_confirm.append(item)
            else:
                item = f"{section_label}: {value}"
                if status == "confirmed":
                    confirmed.append(item)
                else:
                    to_confirm.append(item)
        
        return {
            "review": {
                "confirmed": confirmed if confirmed else ["Nessun dato confermato"],
                "to_confirm": to_confirm if to_confirm else []
            }
        }
