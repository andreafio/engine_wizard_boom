"""API models for requests and responses."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# Session endpoints
class StartSessionRequest(BaseModel):
    """Request to start a new session."""
    context: Dict[str, Any] = Field(default_factory=dict)
    consent: Dict[str, bool] = Field(default_factory=dict)


class StartSessionResponse(BaseModel):
    """Response from starting a session."""
    session_id: str
    wizard: Dict[str, Any]


# Wizard turn endpoints
class UIEvent(BaseModel):
    """UI event from frontend."""
    type: str  # selected_option, multi_selected, text_submitted, etc.
    field: str
    value: Any


class WizardTurnRequest(BaseModel):
    """Request for wizard turn."""
    session_id: str
    event_id: str
    user_message: Optional[str] = None
    ui_event: Optional[UIEvent] = None
    context: Dict[str, Any] = Field(default_factory=dict)


class WizardTurnResponse(BaseModel):
    """Response from wizard turn."""
    assistant_message: str
    wizard: Dict[str, Any]


# Confirm endpoint
class ConfirmRequest(BaseModel):
    """Request to confirm or edit."""
    session_id: str
    event_id: str
    action: str  # confirm or edit
    step: str = "review"


class ConfirmResponse(BaseModel):
    """Response from confirmation."""
    status: str
    message: str
    wizard: Optional[Dict[str, Any]] = None


# Generate endpoint
class GenerateRequest(BaseModel):
    """Request to generate output."""
    session_id: str
    event_id: str
    format: str = "json"  # json, html, pdf


class GenerateResponse(BaseModel):
    """Response with generated output."""
    presentation: Dict[str, Any]
    report: Dict[str, Any]


# Error response
class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: Optional[str] = None
    event_id: Optional[str] = None
