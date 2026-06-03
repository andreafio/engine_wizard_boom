"""Wizard turn and generation API routes."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from app.api.models import (
    WizardTurnRequest, WizardTurnResponse,
    ConfirmRequest, ConfirmResponse,
    GenerateRequest, GenerateResponse
)
from app.core.security import verify_tenant
from app.core.logging import get_logger
from app.core.config import settings
from app.storage.redis_store import redis_store
from app.wizard.flow import build_wizard_state, process_field_update, advance_step, is_step_complete
from app.wizard.extraction import extract_from_ui_event, extract_from_user_message, validate_field_value
from app.wizard.schema import WizardStep, get_next_step
from app.wizard.ui import get_next_required_field, build_assistant_message
from app.llm.provider import ProviderFactory
from app.services.generation_service import GenerationService
from app.services.orchestrator_service import OrchestratorService
from app.services.orchestrator_service_v2 import OrchestratorServiceV2, TurnInput
from app.services.field_extractor_service import FieldExtractorService
from app.services.clarifier_service import ClarifierService
from app.services.quality_critic_service import QualityCriticService
from app.services.blueprint_review_service import BlueprintReviewService
from app.services.strategic_profile_service import StrategicProfileService
from app.services.input_normalizer_service import InputNormalizerService
from app.storage.session_store_adapter import RedisSessionStoreAdapter
from app.db.lead_repository import save_lead

logger = get_logger(__name__)
router = APIRouter(prefix="/v1/wizard", tags=["wizard"])


def _build_llm_provider():
    """Build LLM provider from settings. Returns None if no key configured."""
    if settings.llm_provider == "openai" and settings.openai_api_key:
        return ProviderFactory.create("openai", settings.openai_api_key, settings.openai_model)
    elif settings.llm_provider == "gemini" and settings.gemini_api_key:
        return ProviderFactory.create("gemini", settings.gemini_api_key, settings.gemini_model)
    elif settings.llm_provider == "claude" and settings.anthropic_api_key:
        return ProviderFactory.create("claude", settings.anthropic_api_key, settings.anthropic_model)
    return None


def _build_orchestrator_v2() -> Optional[OrchestratorServiceV2]:
    """Build OrchestratorServiceV2 if an LLM provider is configured."""
    llm_provider = _build_llm_provider()
    if not llm_provider:
        return None
    return OrchestratorServiceV2(
        session_store=RedisSessionStoreAdapter(redis_store),
        field_extractor_service=FieldExtractorService(llm_provider),
        clarifier_service=ClarifierService(llm_provider),
        quality_critic_service=QualityCriticService(llm_provider),
        blueprint_review_service=BlueprintReviewService(llm_provider),
        strategic_profile_service=StrategicProfileService(llm_provider),
        input_normalizer_service=InputNormalizerService(),
    )


@router.post("/turn", response_model=WizardTurnResponse)
async def wizard_turn(
    request: WizardTurnRequest,
    tenant_id: str = Depends(verify_tenant)
):
    """Process a wizard turn.

    Handles user input (via ui_event or user_message), updates state,
    and returns next UI directive.
    """
    # Check idempotency (Redis-backed, survives restarts and multi-instance deploys)
    cached = await redis_store.get_idempotent(request.event_id)
    if cached:
        logger.debug("duplicate_event", event_id=request.event_id)
        return WizardTurnResponse(**cached)

    # Get session (needed for tenant check and V1 fallback)
    session = await redis_store.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # --- V2 path: OrchestratorServiceV2 with intelligent services ---
    orchestrator_v2 = _build_orchestrator_v2()
    if orchestrator_v2:
        try:
            turn_input = TurnInput(
                session_id=request.session_id,
                event_id=request.event_id,
                ui_event=request.ui_event.model_dump() if request.ui_event else None,
                user_message=request.user_message,
                context=request.context or {},
            )
            turn_output = await orchestrator_v2.handle_turn(tenant_id, turn_input)
            response = WizardTurnResponse(
                assistant_message=turn_output.assistant_message,
                wizard=turn_output.wizard,
            )
            await redis_store.put_idempotent(request.event_id, response.model_dump())
            logger.info("v2_turn_processed", session_id=request.session_id)
            return response
        except Exception as e:
            logger.warning("v2_turn_failed_fallback_v1",
                           session_id=request.session_id, error=str(e))
            # Fall through to V1 path
    
    # Extract field and value from input
    field_name = None
    field_value = None
    confidence = "high"
    
    if request.ui_event:
        # Preferred path: structured UI event
        field_name, field_value = extract_from_ui_event(request.ui_event.model_dump())
        confidence = "high"
    elif request.user_message:
        # Fallback: Use orchestrator to extract from free text
        try:
            # Initialize LLM provider for orchestrator
            llm_provider = None
            if settings.llm_provider == "openai" and settings.openai_api_key:
                llm_provider = ProviderFactory.create("openai", settings.openai_api_key, settings.openai_model)
            elif settings.llm_provider == "gemini" and settings.gemini_api_key:
                llm_provider = ProviderFactory.create("gemini", settings.gemini_api_key, settings.gemini_model)
            elif settings.llm_provider == "claude" and settings.anthropic_api_key:
                llm_provider = ProviderFactory.create("claude", settings.anthropic_api_key, settings.anthropic_model)
            
            if llm_provider:
                # Use orchestrator service
                orchestrator = OrchestratorService(llm_provider)
                extraction_result = await orchestrator.extract_field(
                    request.user_message,
                    session
                )
                
                # Get extracted field
                extracted_fields = extraction_result.get("extracted_fields", {})
                if extracted_fields:
                    field_name = list(extracted_fields.keys())[0]
                    field_value = extracted_fields[field_name]
                    confidence = extraction_result.get("confidence", "low")
                    
                    logger.info("orchestrator_extraction",
                               session_id=request.session_id,
                               field=field_name,
                               confidence=confidence)
                else:
                    # No extraction possible
                    logger.warning("orchestrator_no_extraction", 
                                  session_id=request.session_id,
                                  message=request.user_message)
            else:
                # No LLM available, fallback to simple extraction
                section = session.get_blueprint_section(session.current_step)
                current_values = section.value if section and isinstance(section.value, dict) else {}
                next_field = get_next_required_field(session.current_step, current_values)
                field_name, field_value = extract_from_user_message(
                    request.user_message,
                    session.current_step,
                    next_field
                )
                confidence = "low"
                
        except Exception as e:
            logger.error("extraction_failed", 
                        session_id=request.session_id,
                        error=str(e))
            # Fallback to basic extraction
            section = session.get_blueprint_section(session.current_step)
            current_values = section.value if section and isinstance(section.value, dict) else {}
            next_field = get_next_required_field(session.current_step, current_values)
            field_name, field_value = extract_from_user_message(
                request.user_message,
                session.current_step,
                next_field
            )
            confidence = "low"
    
    if not field_name or field_value is None:
        raise HTTPException(status_code=400, detail="No valid input provided")
    
    # Validate field value
    is_valid, error_msg = validate_field_value(field_name, field_value, session.current_step)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    # Update blueprint
    success, msg = process_field_update(session, field_name, field_value)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    
    # Check if step is complete and advance if so
    if is_step_complete(session, session.current_step):
        advance_step(session)
    
    # Build response
    wizard_state = build_wizard_state(session)
    
    # Determine assistant message
    section = session.get_blueprint_section(session.current_step)
    current_values = section.value if section and isinstance(section.value, dict) else {}
    next_field = get_next_required_field(session.current_step, current_values)
    
    if next_field:
        assistant_msg = build_assistant_message(session.current_step, next_field)
    else:
        assistant_msg = "Perfetto! Proseguiamo."
    
    # Add to conversation buffer
    session.add_turn(
        user_message=request.user_message,
        assistant_message=assistant_msg,
        ui_event=request.ui_event.model_dump() if request.ui_event else None
    )
    
    # Save session
    await redis_store.save_session(session)
    
    # Build response
    response = WizardTurnResponse(
        assistant_message=assistant_msg,
        wizard=wizard_state.model_dump()
    )
    
    # Cache for idempotency (Redis-backed)
    await redis_store.put_idempotent(request.event_id, response.model_dump())

    logger.info("turn_processed",
                session_id=request.session_id,
                field=field_name,
                step=session.current_step)
    
    return response


@router.post("/confirm", response_model=ConfirmResponse)
async def confirm(
    request: ConfirmRequest,
    tenant_id: str = Depends(verify_tenant)
):
    """Confirm or edit the review step."""
    # Get session
    session = await redis_store.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if session.current_step != WizardStep.REVIEW:
        raise HTTPException(status_code=400, detail="Not in review step")
    
    if request.action == "confirm":
        # Mark review as confirmed and move to completed
        session.mark_step_confirmed(WizardStep.REVIEW)
        session.current_step = WizardStep.COMPLETED
        await redis_store.save_session(session)
        
        logger.info("wizard_confirmed", session_id=request.session_id)
        
        return ConfirmResponse(
            status="confirmed",
            message="Wizard completato! Procedi alla generazione."
        )
    
    elif request.action == "edit":
        # Go back to first step for editing
        session.current_step = WizardStep.CONTEXT
        await redis_store.save_session(session)
        
        wizard_state = build_wizard_state(session)
        
        logger.info("wizard_edit_mode", session_id=request.session_id)
        
        return ConfirmResponse(
            status="editing",
            message="Torna indietro per modificare.",
            wizard=wizard_state.model_dump()
        )
    
    else:
        raise HTTPException(status_code=400, detail="Invalid action")


@router.post("/generate", response_model=GenerateResponse)
async def generate(
    request: GenerateRequest,
    tenant_id: str = Depends(verify_tenant)
):
    """Generate final presentation and report."""
    # Get session
    session = await redis_store.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if session.current_step != WizardStep.COMPLETED:
        raise HTTPException(status_code=400, detail="Wizard not completed yet")
    
    # Initialize LLM provider
    llm_provider = None
    try:
        if settings.llm_provider == "openai" and settings.openai_api_key:
            llm_provider = ProviderFactory.create("openai", settings.openai_api_key, settings.openai_model)
        elif settings.llm_provider == "gemini" and settings.gemini_api_key:
            llm_provider = ProviderFactory.create("gemini", settings.gemini_api_key, settings.gemini_model)
        elif settings.llm_provider == "claude" and settings.anthropic_api_key:
            llm_provider = ProviderFactory.create("claude", settings.anthropic_api_key, settings.anthropic_model)
        else:
            raise HTTPException(status_code=500, detail="No LLM provider configured")
    except Exception as e:
        logger.error("llm_init_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to initialize LLM")
    
    # Generate output (slides + report)
    generation_service = GenerationService(llm_provider)
    try:
        output = await generation_service.generate_output(session, request.format)
        logger.info("generation_completed", session_id=request.session_id)
    except Exception as e:
        logger.error("generation_failed", session_id=request.session_id, error=str(e))
        raise HTTPException(status_code=500, detail="Generation failed")

    # Generate strategic profile V2 (consulting-grade) — non-blocking
    internal_profile = None
    orchestrator_v2 = _build_orchestrator_v2()
    if orchestrator_v2:
        try:
            internal_profile = await orchestrator_v2.handle_generate_internal(
                tenant_id=tenant_id,
                session_id=request.session_id,
                event_id=f"{request.event_id}_profile",
            )
            logger.info("internal_profile_generated", session_id=request.session_id)
        except Exception as e:
            logger.warning("internal_profile_failed", session_id=request.session_id, error=str(e))

    await save_lead(
        session=session,
        presentation=output.get("presentation", {}),
        report=output.get("report", {}),
        internal_profile=internal_profile,
    )

    return GenerateResponse(
        presentation=output.get("presentation", {}),
        report=output.get("report", {}),
        internal_profile=internal_profile,
    )
