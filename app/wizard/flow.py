"""Wizard flow control and validation logic."""
from typing import Dict, List, Optional, Tuple
from app.wizard.schema import (
    WizardStep, FieldStatus, ValidationResult, WizardState,
    get_next_step, calculate_progress, get_step_schema
)
from app.wizard.state import Session
from app.wizard.ui import (
    build_ui_directive, get_next_required_field,
    get_all_required_fields, build_assistant_message, build_review_ui
)


def validate_step(session: Session, step: WizardStep) -> ValidationResult:
    """Validate if a step is complete.
    
    Args:
        session: Current session
        step: Step to validate
        
    Returns:
        ValidationResult with required fields and errors
    """
    validation = ValidationResult()
    
    # Get current values for this step
    section = session.get_blueprint_section(step)
    current_values = section.value if section and isinstance(section.value, dict) else {}
    
    # Get required fields
    required_fields = get_all_required_fields(step)
    
    # Check which fields are missing
    for field in required_fields:
        if field not in current_values or current_values[field] is None:
            validation.required_fields.append(field)
            validation.errors.append(f"Campo obbligatorio: {field}")
    
    return validation


def is_step_complete(session: Session, step: WizardStep) -> bool:
    """Check if a step has all required fields filled.
    
    Args:
        session: Current session
        step: Step to check
        
    Returns:
        True if all required fields are present
    """
    validation = validate_step(session, step)
    return len(validation.required_fields) == 0


def advance_step(session: Session) -> bool:
    """Advance to next step if current step is complete.
    
    Args:
        session: Current session
        
    Returns:
        True if advanced, False if not ready
    """
    if not is_step_complete(session, session.current_step):
        return False
    
    # Mark current step as confirmed
    session.mark_step_confirmed(session.current_step)
    
    # Move to next step
    next_step = get_next_step(session.current_step)
    if next_step:
        session.current_step = next_step
        return True
    
    return False


def build_wizard_state(session: Session) -> WizardState:
    """Build the complete wizard state for frontend.
    
    Args:
        session: Current session
        
    Returns:
        WizardState object with all info for rendering
    """
    step = session.current_step
    
    # Get current values for this step
    section = session.get_blueprint_section(step)
    current_values = section.value if section and isinstance(section.value, dict) else {}
    
    # Determine what to ask next
    if step == WizardStep.REVIEW:
        ui_directive = build_review_ui()
        assistant_msg = "Ecco un riepilogo delle tue risposte. Confermi?"
    else:
        next_field = get_next_required_field(step, current_values)
        if next_field:
            ui_directive = build_ui_directive(step, next_field, current_values)
            assistant_msg = build_assistant_message(step, next_field)
        else:
            # All fields filled, should advance
            ui_directive = build_ui_directive(step, list(current_values.keys())[0] if current_values else "")
            assistant_msg = "Perfetto! Proseguiamo."
    
    # Validate current step
    validation = validate_step(session, step)
    
    # Build events
    events = []
    if section and section.status == FieldStatus.CONFIRMED:
        events.append({"type": "saved", "label": "Salvato ✓"})
    
    return WizardState(
        wizard_id="strategic_snapshot_v1",
        current_step=step,
        progress=calculate_progress(step),
        blueprint=session.blueprint,
        ui=ui_directive,
        validation=validation,
        events=events
    )


def process_field_update(
    session: Session,
    field: str,
    value: any,
    step: Optional[WizardStep] = None
) -> Tuple[bool, str]:
    """Process a field update from user input.
    
    Args:
        session: Current session
        field: Field name being updated
        value: New value
        step: Step to update (defaults to current_step)
        
    Returns:
        Tuple of (success, message)
    """
    if step is None:
        step = session.current_step
    
    # Get current section value
    section = session.get_blueprint_section(step)
    current_values = section.value if section and isinstance(section.value, dict) else {}
    
    # Update the field
    current_values[field] = value
    
    # Save back to blueprint
    session.update_blueprint_section(step, current_values, FieldStatus.DRAFT)
    
    return True, f"Campo {field} aggiornato"
