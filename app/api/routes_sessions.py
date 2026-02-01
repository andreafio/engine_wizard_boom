"""Session management API routes."""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from app.api.models import StartSessionRequest, StartSessionResponse, ErrorResponse
from app.core.security import verify_tenant
from app.core.logging import get_logger
from app.storage.redis_store import redis_store
from app.wizard.state import Session
from app.wizard.schema import WizardStep
from app.wizard.flow import build_wizard_state

logger = get_logger(__name__)
router = APIRouter(prefix="/v1/sessions", tags=["sessions"])


@router.post("/start", response_model=StartSessionResponse)
async def start_session(
    request: StartSessionRequest,
    tenant_id: str = Depends(verify_tenant)
):
    """Start a new wizard session.
    
    Creates a new session with initial state and returns the first wizard step.
    """
    # Generate session ID
    session_id = f"sess_{uuid.uuid4().hex[:16]}"
    
    # Create new session
    session = Session(
        session_id=session_id,
        tenant_id=tenant_id,
        current_step=WizardStep.CONTEXT,
        context=request.context,
        consent=request.consent
    )
    
    # Save to Redis
    success = await redis_store.save_session(session)
    if not success:
        logger.error("session_save_failed", session_id=session_id)
        raise HTTPException(status_code=500, detail="Failed to create session")
    
    # Build initial wizard state
    wizard_state = build_wizard_state(session)
    
    logger.info("session_started", session_id=session_id, tenant_id=tenant_id)
    
    return StartSessionResponse(
        session_id=session_id,
        wizard=wizard_state.model_dump()
    )


@router.get("/{session_id}", response_model=dict)
async def get_session(
    session_id: str,
    tenant_id: str = Depends(verify_tenant)
):
    """Get current session state."""
    session = await redis_store.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    wizard_state = build_wizard_state(session)
    
    return {
        "session_id": session_id,
        "wizard": wizard_state.model_dump()
    }


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    tenant_id: str = Depends(verify_tenant)
):
    """Delete a session."""
    session = await redis_store.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    await redis_store.delete_session(session_id)
    
    logger.info("session_deleted", session_id=session_id)
    
    return {"status": "deleted", "session_id": session_id}
