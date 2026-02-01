"""Wizard state models and session management."""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.wizard.schema import Blueprint, WizardStep, FieldStatus


class ConversationTurn(BaseModel):
    """A single conversation turn."""
    timestamp: datetime
    user_message: Optional[str] = None
    assistant_message: str
    ui_event: Optional[Dict[str, Any]] = None


class Session(BaseModel):
    """Wizard session state."""
    session_id: str
    tenant_id: str
    current_step: WizardStep = WizardStep.CONTEXT
    blueprint: Blueprint = Field(default_factory=Blueprint)
    conversation_buffer: List[ConversationTurn] = Field(default_factory=list, max_length=10)
    context: Dict[str, Any] = Field(default_factory=dict)  # page_url, utm params, etc.
    consent: Dict[str, bool] = Field(default_factory=dict)  # gdpr, profiling
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def add_turn(self, user_message: Optional[str], assistant_message: str, ui_event: Optional[Dict] = None):
        """Add a conversation turn to the buffer."""
        turn = ConversationTurn(
            timestamp=datetime.utcnow(),
            user_message=user_message,
            assistant_message=assistant_message,
            ui_event=ui_event
        )
        self.conversation_buffer.append(turn)
        # Keep only last N turns
        if len(self.conversation_buffer) > 10:
            self.conversation_buffer = self.conversation_buffer[-10:]
        self.updated_at = datetime.utcnow()
    
    def get_blueprint_section(self, step: WizardStep):
        """Get blueprint section for a step."""
        section_map = {
            WizardStep.CONTEXT: self.blueprint.context,
            WizardStep.OBJECTIVE: self.blueprint.objective,
            WizardStep.TARGET_MARKET: self.blueprint.target_market,
            WizardStep.VALUE_PROP: self.blueprint.value_prop,
            WizardStep.CHANNELS_ASSETS: self.blueprint.channels_assets,
            WizardStep.CONSTRAINTS: self.blueprint.constraints,
        }
        return section_map.get(step)
    
    def update_blueprint_section(self, step: WizardStep, value: Dict[str, Any], status: FieldStatus = FieldStatus.DRAFT):
        """Update a blueprint section."""
        section = self.get_blueprint_section(step)
        if section is not None:
            section.value = value
            section.status = status
            self.updated_at = datetime.utcnow()
    
    def mark_step_confirmed(self, step: WizardStep):
        """Mark a step as confirmed."""
        section = self.get_blueprint_section(step)
        if section is not None:
            section.status = FieldStatus.CONFIRMED
            self.updated_at = datetime.utcnow()


class EventLog(BaseModel):
    """Event for analytics and debugging."""
    event_id: str
    session_id: str
    tenant_id: str
    event_type: str  # turn_received, state_updated, step_completed, generate_started, etc.
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
