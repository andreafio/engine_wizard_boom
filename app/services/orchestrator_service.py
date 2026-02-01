"""Orchestrator service for extracting structured data from user input."""
from typing import Any, Dict, List, Optional, Tuple
from pydantic import ValidationError
from app.llm.provider import LLMProvider
from app.llm.prompts import build_extraction_prompt, ORCHESTRATOR_SYSTEM_PROMPT
from app.services.orchestrator_schema import OrchestratorOutput
from app.services.field_extractor_service import FieldExtractorService, FieldExtractionResult
from app.wizard.schema import WizardStep, get_step_schema
from app.wizard.state import Session
from app.core.logging import get_logger

logger = get_logger(__name__)


class OrchestratorService:
    """Service for orchestrating field extraction from free text."""
    
    def __init__(self, llm_provider: LLMProvider):
        """Initialize orchestrator service.
        
        Args:
            llm_provider: LLM provider instance
        """
        self.llm = llm_provider
        self.field_extractor = FieldExtractorService(llm_provider)
    
    async def extract_single_field(
        self,
        user_message: str,
        session: Session,
        field_path: str
    ) -> FieldExtractionResult:
        """Extract a single field using the strict field extractor.
        
        Args:
            user_message: User's input message
            session: Current session
            field_path: Full field path like "context.industry"
            
        Returns:
            FieldExtractionResult
        """
        # Parse field path
        section_name, field_name = field_path.split('.', 1)
        section_enum = WizardStep(section_name.lower())
        
        # Get field schema
        schema = get_step_schema(section_enum)
        if not schema or field_name not in schema["fields"]:
            raise ValueError(f"Field {field_path} not found in schema")
            
        field_def = schema["fields"][field_name]
        ui_type = field_def.get("type", "short_text")
        options = field_def.get("options", [])
        
        # Get current blueprint snippet
        blueprint_section = session.get_blueprint_section(section_enum)
        blueprint_snippet = blueprint_section.value if blueprint_section else {}
        
        # Extract field
        return await self.field_extractor.extract_field(
            current_section=section_enum.value,
            current_field=field_path,
            ui_type=ui_type,
            options=options,
            user_message=user_message,
            blueprint_snippet=blueprint_snippet
        )
    
    async def extract_field(
        self,
        user_message: str,
        session: Session,
        expected_field: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract structured field from user's free text message.
        
        This is used as a fallback when user provides text instead of
        using the UI components. The orchestrator ONLY extracts data
        relevant to the current step - it never skips ahead or invents info.
        
        For single field extraction, uses the strict FieldExtractorService
        when expected_field is provided and supported.
        
        Args:
            user_message: User's free text input
            session: Current session with wizard state
            expected_field: The field we expect (from current step)
            
        Returns:
            Dict with extracted_fields, confidence, suggested_options
        """
        # If specific field requested and it's a full path, use strict field extractor
        if expected_field and '.' in expected_field:
            try:
                field_result = await self.extract_single_field(
                    user_message=user_message,
                    session=session,
                    field_path=expected_field
                )
                
                # Convert to legacy format for backward compatibility
                legacy_result = {
                    "extracted_fields": {expected_field: field_result.value} if field_result.value is not None else {},
                    "field_status": {expected_field: field_result.status},
                    "confidence": "high" if field_result.confidence > 0.7 else "medium" if field_result.confidence > 0.4 else "low",
                    "suggested_options": field_result.suggested_clarifier.options if field_result.suggested_clarifier else []
                }
                
                # Add quality critique if available
                if field_result.quality_critique:
                    legacy_result["quality_score"] = field_result.quality_critique.quality_score
                    legacy_result["recommend_deep_followup"] = field_result.quality_critique.recommend_deep
                    legacy_result["followup_field"] = field_result.quality_critique.recommended_followup_field
                    legacy_result["quality_reason"] = field_result.quality_critique.reason
                
                return legacy_result
            except Exception as e:
                logger.warning("strict_extraction_failed", field=expected_field, error=str(e))
                # Fall back to legacy extraction
        
        # Legacy extraction logic continues below...
        current_step = session.current_step
        step_schema = get_step_schema(current_step)
        if not step_schema:
            logger.warning("orchestrator_no_schema", step=current_step)
            return {
                "extracted_fields": {},
                "confidence": "low",
                "suggested_options": []
            }
        
        # If no expected field provided, get the next required one
        if not expected_field:
            section = session.get_blueprint_section(current_step)
            current_values = section.value if section and isinstance(section.value, dict) else {}
            
            # Find first missing required field
            for field_name, field_def in step_schema["fields"].items():
                if field_def.get("required", False):
                    if field_name not in current_values or current_values[field_name] is None:
                        expected_field = field_name
                        break
        
        if not expected_field:
            logger.warning("orchestrator_no_field", step=current_step)
            return {
                "extracted_fields": {},
                "confidence": "low",
                "suggested_options": []
            }
        
        # Build context for the orchestrator
        field_def = step_schema["fields"].get(expected_field, {})
        context = {
            "current_step": current_step.value,
            "field_type": field_def.get("type"),
            "field_label": field_def.get("label"),
            "field_options": field_def.get("options", []),
            "blueprint_summary": self._build_blueprint_summary(session)
        }
        
        # Call LLM orchestrator
        try:
            prompt = build_extraction_prompt(user_message, expected_field, context)
            result = await self.llm.generate_json(
                prompt=prompt,
                system_prompt=ORCHESTRATOR_SYSTEM_PROMPT
            )
            
            # Normalize result to ensure backward compatibility
            if "field_status" not in result:
                # Legacy format: add field_status based on confidence
                result["field_status"] = {}
                confidence = result.get("confidence", "low")
                for field in result.get("extracted_fields", {}).keys():
                    result["field_status"][field] = "confirmed" if confidence == "high" else "draft"
            
            # Validate with Pydantic schema
            try:
                validated_output = OrchestratorOutput.model_validate(result)
                result = validated_output.model_dump()
            except ValidationError as ve:
                logger.warning("orchestrator_validation_failed",
                             step=current_step,
                             field=expected_field,
                             errors=ve.errors())
                # Continue with unvalidated result as fallback
            
            logger.info("orchestrator_extracted",
                       step=current_step,
                       field=expected_field,
                       confidence=result.get("confidence", "unknown"),
                       status=result.get("field_status", {}).get(expected_field, "unknown"))
            
            return result
            
            return result
            
        except Exception as e:
            logger.error("orchestrator_failed",
                        step=current_step,
                        field=expected_field,
                        error=str(e))
            
            # Fallback: return raw text as value with draft status
            return {
                "extracted_fields": {expected_field: user_message},
                "field_status": {expected_field: "draft"},
                "confidence": "low",
                "suggested_options": []
            }
    
    async def extract_single_field(
        self,
        user_message: str,
        session: Session,
        field_path: str
    ) -> FieldExtractionResult:
        """
        Extract a single field using strict field extractor.
        
        This uses the new FieldExtractorService for more precise,
        field-specific extraction with better validation.
        
        Args:
            user_message: User's free text input
            session: Current session
            field_path: Dot notation field path (e.g., "context.industry")
            
        Returns:
            FieldExtractionResult with extracted value
        """
        current_step = session.current_step
        
        # Get step schema
        step_schema = get_step_schema(current_step)
        if not step_schema:
            logger.warning("no_schema_for_step", step=current_step)
            return FieldExtractionResult(
                field=field_path,
                value=None,
                status="draft",
                confidence=0.0,
                evidence="no schema available",
                needs_clarification=True
            )
        
        # Parse field path to get section and field name
        field_parts = field_path.split('.')
        if len(field_parts) < 2:
            # Legacy format: assume context section
            section_name = "context"
            field_name = field_path
            full_field_path = f"context.{field_path}"
        else:
            section_name = field_parts[0]
            field_name = '.'.join(field_parts[1:])
            full_field_path = field_path
        
        # Get field definition
        field_def = step_schema["fields"].get(field_name)
        if not field_def:
            logger.warning("field_not_in_schema", field=field_name, step=current_step)
            return FieldExtractionResult(
                field=field_path,
                value=None,
                status="draft",
                confidence=0.0,
                evidence="field not defined in schema",
                needs_clarification=True
            )
        
        # Get current field state from blueprint
        blueprint_section = session.get_blueprint_section(current_step)
        current_field_state = {"field_state": {"value": None, "status": "missing", "confidence": 0.0}}
        
        if blueprint_section and isinstance(blueprint_section.value, dict):
            current_value = blueprint_section.value.get(field_name)
            current_field_state = {
                "field_state": {
                    "value": current_value,
                    "status": "confirmed" if current_value is not None else "missing",
                    "confidence": 1.0 if current_value is not None else 0.0
                }
            }
        
        # Extract using field extractor service
        # Extract context for clarifier
        context = self._extract_context_for_clarifier(session)
        
        result = await self.field_extractor.extract_field(
            current_section=section_name,
            current_field=full_field_path,
            ui_type=field_def.get("ui_type", "short_text"),
            options=field_def.get("options", []),
            user_message=user_message,
            blueprint_snippet=current_field_state,
            context=context
        )
        
        # Update field path in result to match input
        result.field = field_path
        return result
    
    def _extract_context_for_clarifier(self, session: Session) -> Dict[str, Any]:
        """Extract relevant context for clarifier from session/blueprint.
        
        Args:
            session: Current session
            
        Returns:
            Dict with context information (industry, business_model, etc.)
        """
        context = {}
        
        # Extract from completed blueprint sections
        for step_name in ["context", "objective", "target_market", "value_prop"]:
            try:
                from app.wizard.schema import WizardStep
                step_enum = WizardStep(step_name)
                section = session.get_blueprint_section(step_enum)
                if section and section.value and isinstance(section.value, dict):
                    # Extract common context fields
                    if "industry" in section.value and section.value["industry"]:
                        context["industry"] = section.value["industry"]
                    if "business_model" in section.value and section.value["business_model"]:
                        context["business_model"] = section.value["business_model"]
                    if "offer_type" in section.value and section.value["offer_type"]:
                        context["offer_type"] = section.value["offer_type"]
                    if "target_role" in section.value and section.value["target_role"]:
                        context["target_role"] = section.value["target_role"]
            except (ValueError, AttributeError):
                continue
        
        return context
    
    def _build_blueprint_summary(self, session: Session) -> Dict[str, Any]:
        """Build a summary of completed blueprint sections.
        
        This gives the orchestrator context about what's already been captured,
        helping it make better extraction decisions.
        
        Args:
            session: Current session
            
        Returns:
            Dictionary with completed sections
        """
        summary = {}
        
        for step_name in ["context", "objective", "target_market", "value_prop", 
                          "channels_assets", "constraints"]:
            try:
                step_enum = WizardStep(step_name)
                section = session.get_blueprint_section(step_enum)
                if section and section.value and section.status.value == "confirmed":
                    summary[step_name] = section.value
            except (ValueError, AttributeError):
                continue
        
        return summary
    
    async def suggest_options(
        self,
        user_message: str,
        field_name: str,
        available_options: List[Dict[str, str]],
        context: Dict[str, Any]
    ) -> List[str]:
        """Suggest most likely options based on vague user input.
        
        When user input is unclear, the orchestrator suggests 2-3 most
        relevant options from the available choices.
        
        Args:
            user_message: User's vague input
            field_name: Field being asked about
            available_options: List of valid options with id/label
            context: Additional context
            
        Returns:
            List of suggested option IDs (2-3 items)
        """
        prompt = f"""User input: "{user_message}"

Field: {field_name}

Available options:
{chr(10).join([f"- {opt['id']}: {opt['label']}" for opt in available_options])}

Context: {context}

Based on the user's vague input, suggest the 2-3 most likely options they meant.

Return JSON:
{{
  "suggested_option_ids": ["id1", "id2", "id3"]
}}"""
        
        try:
            result = await self.llm.generate_json(
                prompt=prompt,
                system_prompt=ORCHESTRATOR_SYSTEM_PROMPT
            )
            
            suggestions = result.get("suggested_option_ids", [])
            # Return max 3 suggestions
            return suggestions[:3]
            
        except Exception as e:
            logger.error("suggestion_failed", field=field_name, error=str(e))
            # Fallback: return first 2 options
            return [opt["id"] for opt in available_options[:2]]
