"""Generation service for creating presentations and reports."""
import json
import re
from typing import Dict, Any
from pydantic import ValidationError
from app.llm.provider import LLMProvider
from app.llm.prompts import build_generation_prompt, GENERATOR_SYSTEM_PROMPT
from app.llm.schemas import GenerationOutput
from app.services.generation_guardrails import apply_all_guardrails, check_blueprint_has_metrics
from app.wizard.state import Session
from app.core.logging import get_logger

logger = get_logger(__name__)


class GenerationService:
    """Service for generating final outputs."""
    
    def __init__(self, llm_provider: LLMProvider):
        """Initialize generation service.
        
        Args:
            llm_provider: LLM provider instance
        """
        self.llm = llm_provider
    
    def _extract_confirmed_fields_only(self, blueprint_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Extract only confirmed fields from blueprint.
        
        Ensures generator receives validated data only, not draft or unconfirmed fields.
        
        Args:
            blueprint_dict: Raw blueprint data
            
        Returns:
            Cleaned blueprint with only confirmed fields
        """
        confirmed = {}
        
        for section_key, section_value in blueprint_dict.items():
            if isinstance(section_value, dict):
                # Only include fields that are not empty/null
                confirmed[section_key] = {
                    k: v for k, v in section_value.items()
                    if v not in (None, '', [], {})
                }
            elif section_value not in (None, '', [], {}):
                confirmed[section_key] = section_value
        
        return confirmed
    
    def _parse_json_robust(self, raw_response: str) -> Dict[str, Any]:
        """Parse JSON with robust error handling.
        
        Handles common LLM output issues:
        - Markdown code blocks
        - Trailing text
        - Multiple JSON objects
        
        Args:
            raw_response: Raw LLM response
            
        Returns:
            Parsed JSON dict
            
        Raises:
            ValueError: If JSON cannot be extracted
        """
        # Strip markdown code blocks
        cleaned = re.sub(r'^```(?:json)?\s*', '', raw_response, flags=re.MULTILINE)
        cleaned = re.sub(r'\s*```$', '', cleaned, flags=re.MULTILINE)
        
        # Try direct parse first
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
        
        # Try to extract first JSON object
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.finditer(json_pattern, cleaned, re.DOTALL)
        
        for match in matches:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                continue
        
        raise ValueError("No valid JSON found in LLM response")
    
    async def generate_output(self, session: Session, format: str = "json") -> Dict[str, Any]:
        """Generate presentation and report from blueprint.
        
        BLUEPRINT-ONLY GENERATION:
        - Only confirmed fields are passed to LLM
        - No conversational buffer or unvalidated notes
        - Explicit confirmed_fields_only section in input
        
        VALIDATION:
        - Pydantic schema validation (GenerationOutput)
        - Guardrails: invented numbers detection
        - Assumptions enforcement when metrics missing
        - Bullet hygiene (max 140 chars, no duplicates)
        
        Args:
            session: Session with confirmed blueprint
            format: Output format (json, html, pdf)
            
        Returns:
            Validated and cleaned output structure
        """
        logger.info("generation_started", session_id=session.session_id, format=format)
        
        # Build blueprint dict with ONLY confirmed fields
        raw_blueprint = {
            "context": session.blueprint.context.value if session.blueprint.context.value else {},
            "objective": session.blueprint.objective.value if session.blueprint.objective.value else {},
            "target_market": session.blueprint.target_market.value if session.blueprint.target_market.value else {},
            "value_prop": session.blueprint.value_prop.value if session.blueprint.value_prop.value else {},
            "channels_assets": session.blueprint.channels_assets.value if session.blueprint.channels_assets.value else {},
            "constraints": session.blueprint.constraints.value if session.blueprint.constraints.value else {},
        }
        
        # Extract only confirmed, non-empty fields
        blueprint_dict = self._extract_confirmed_fields_only(raw_blueprint)
        
        logger.info("blueprint_extracted",
                   session_id=session.session_id,
                   has_metrics=check_blueprint_has_metrics(blueprint_dict),
                   fields_count=sum(len(v) if isinstance(v, dict) else 1 for v in blueprint_dict.values()))
        
        # Try generation with retry
        max_attempts = 2
        last_error = None
        
        for attempt in range(1, max_attempts + 1):
            try:
                # Generate using LLM
                prompt = build_generation_prompt(blueprint_dict)
                raw_result = await self.llm.generate_json(
                    prompt=prompt,
                    system_prompt=GENERATOR_SYSTEM_PROMPT
                )
                
                # If generate_json returns dict directly, use it
                # Otherwise parse if it's a string
                if isinstance(raw_result, str):
                    parsed_result = self._parse_json_robust(raw_result)
                else:
                    parsed_result = raw_result
                
                # Apply guardrails BEFORE validation
                cleaned_result = apply_all_guardrails(parsed_result, blueprint_dict)
                
                # Validate with Pydantic schema
                validated_output = GenerationOutput.model_validate(cleaned_result)
                
                logger.info("generation_completed",
                           session_id=session.session_id,
                           attempt=attempt,
                           slides_count=len(validated_output.slides),
                           assumptions_count=len(validated_output.assumptions))
                
                # Return as dict
                return validated_output.model_dump()
                
            except (json.JSONDecodeError, ValueError) as e:
                last_error = e
                logger.warning("generation_parse_failed",
                             session_id=session.session_id,
                             attempt=attempt,
                             error=str(e))
                if attempt < max_attempts:
                    continue
                    
            except ValidationError as e:
                last_error = e
                logger.warning("generation_validation_failed",
                             session_id=session.session_id,
                             attempt=attempt,
                             errors=e.errors())
                if attempt < max_attempts:
                    continue
                    
            except Exception as e:
                last_error = e
                logger.error("generation_failed",
                           session_id=session.session_id,
                           attempt=attempt,
                           error=str(e))
                break
        
        # All attempts failed - return validated fallback
        logger.error("generation_all_attempts_failed",
                    session_id=session.session_id,
                    last_error=str(last_error))
        
        fallback = self._get_fallback_output()
        
        # Validate fallback too
        try:
            validated_fallback = GenerationOutput.model_validate(fallback)
            return validated_fallback.model_dump()
        except ValidationError:
            # If even fallback fails validation, return it anyway (should never happen)
            return fallback
    
    def _get_fallback_output(self) -> Dict[str, Any]:
        """Get validated fallback output.
        
        Returns:
            Fallback structure matching GenerationOutput schema
        """
        return {
            "slides": [
                {
                    "title": "Strategia Marketing - Documento Generato",
                    "bullets": [
                        "Documento generato dal Wizard BOOM",
                        "Basato sui dati confermati nel blueprint",
                        "Pronto per la revisione esecutiva"
                    ]
                },
                {
                    "title": "Contesto Aziendale",
                    "bullets": [
                        "Analisi del settore di riferimento",
                        "Posizionamento competitivo",
                        "Opportunità di mercato"
                    ]
                },
                {
                    "title": "Obiettivi Strategici",
                    "bullets": [
                        "Definizione goal primari",
                        "Metriche di successo",
                        "Timeline di esecuzione"
                    ]
                },
                {
                    "title": "Target Market",
                    "bullets": [
                        "Profilazione audience",
                        "Segmentazione geografica",
                        "Pain points identificati"
                    ]
                },
                {
                    "title": "Value Proposition",
                    "bullets": [
                        "Proposta di valore differenziante",
                        "Benefici chiave per il cliente",
                        "Vantaggio competitivo"
                    ]
                },
                {
                    "title": "Next Steps",
                    "bullets": [
                        "Revisione dettagliata della strategia",
                        "Validazione con il team",
                        "Pianificazione implementazione"
                    ]
                }
            ],
            "report_sections": [
                {
                    "title": "Executive Summary",
                    "content": "Report strategico generato automaticamente basato sulle informazioni fornite durante il processo wizard. Si consiglia una revisione dettagliata prima della presentazione al cliente."
                },
                {
                    "title": "Contesto Strategico",
                    "content": "Analisi basata sui dati inseriti nel blueprint confermato. Include valutazione del mercato, posizionamento competitivo e opportunità identificate."
                },
                {
                    "title": "Raccomandazioni",
                    "content": "Azioni strategiche prioritarie per il raggiungimento degli obiettivi. Include roadmap di implementazione e metriche di monitoraggio."
                },
                {
                    "title": "Rischi e Assunzioni",
                    "content": "Identificazione dei principali rischi e delle assunzioni alla base della strategia proposta."
                },
                {
                    "title": "Next Steps",
                    "content": "Revisione strategia con il team, validazione assunzioni, pianificazione implementazione dettagliata."
                }
            ],
            "assumptions": [
                "Generazione LLM fallita - utilizzare questo output come template di fallback",
                "Dati basati esclusivamente sul blueprint confermato",
                "Si consiglia rigenerazione con LLM disponibile"
            ],
            "next_steps": [
                "Rigenerare l'output con LLM disponibile",
                "Revisione manuale della strategia",
                "Validazione con stakeholder",
                "Integrazione dati quantitativi mancanti"
            ]
        }
