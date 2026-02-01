"""Extract structured data from UI events and user messages."""
from typing import Any, Dict, Optional, Tuple
from app.wizard.schema import WizardStep, get_step_schema


def extract_from_ui_event(ui_event: Dict[str, Any]) -> Tuple[Optional[str], Any]:
    """Extract field name and value from UI event.
    
    Args:
        ui_event: UI event dict with type, field, value
        
    Returns:
        Tuple of (field_name, value) or (None, None) if invalid
    """
    event_type = ui_event.get("type")
    field = ui_event.get("field")
    value = ui_event.get("value")
    
    if not field or value is None:
        return None, None
    
    # Normalize value based on event type
    if event_type == "selected_option":
        # Single select
        return field, value
    elif event_type == "multi_selected":
        # Multi select - value should be a list
        if not isinstance(value, list):
            value = [value]
        return field, value
    elif event_type in ["text_submitted", "slider_changed"]:
        # Text or slider
        return field, value
    elif event_type == "clicked":
        # Button click (for confirmation)
        return field, value
    
    return field, value


def extract_from_user_message(
    user_message: str,
    step: WizardStep,
    expected_field: Optional[str] = None
) -> Tuple[Optional[str], Any]:
    """Extract field value from free-text user message.
    
    This is a simple fallback for when ui_event is not provided.
    In a full implementation, this would call LLM for extraction.
    
    Args:
        user_message: User's text input
        step: Current wizard step
        expected_field: The field we're expecting input for
        
    Returns:
        Tuple of (field_name, value)
    """
    if not expected_field:
        # No field specified, just return the message as-is
        # In production, we'd use LLM here to figure out what field this relates to
        return None, user_message
    
    # Simple extraction: just use the message as the value for expected field
    # In production, LLM would parse and structure this
    return expected_field, user_message.strip()


def validate_field_value(
    field: str,
    value: Any,
    step: WizardStep
) -> Tuple[bool, Optional[str]]:
    """Validate a field value against schema constraints.
    
    Args:
        field: Field name
        value: Field value
        step: Current step
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    step_schema = get_step_schema(step)
    if not step_schema or field not in step_schema["fields"]:
        return True, None
    
    field_def = step_schema["fields"][field]
    field_type = field_def.get("type")
    constraints = field_def.get("constraints", {})
    
    # Check required
    if field_def.get("required", False) and not value:
        return False, f"{field} è obbligatorio"
    
    # Validate multi_select constraints
    if field_type == "multi_select" and isinstance(value, list):
        min_items = constraints.get("min", 0)
        max_items = constraints.get("max", float('inf'))
        
        if len(value) < min_items:
            return False, f"Seleziona almeno {min_items} opzioni"
        if len(value) > max_items:
            return False, f"Seleziona al massimo {max_items} opzioni"
    
    # Validate single_select: value must be in options
    if field_type == "single_select" and "options" in field_def:
        valid_ids = [opt["id"] for opt in field_def["options"]]
        if value not in valid_ids:
            return False, f"Valore non valido per {field}"
    
    # Validate multi_select: all values must be in options
    if field_type == "multi_select" and "options" in field_def:
        valid_ids = [opt["id"] for opt in field_def["options"]]
        if isinstance(value, list):
            for v in value:
                if v not in valid_ids:
                    return False, f"Valore non valido: {v}"
    
    return True, None
