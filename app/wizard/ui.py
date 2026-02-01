"""UI directive builders for wizard components."""
from typing import Dict, List, Optional
from app.wizard.schema import (
    UIDirective, UIComponentType, UIOption, UIConstraints,
    WizardStep, get_step_schema
)


def build_ui_directive(step: WizardStep, field_name: str, current_values: Optional[Dict] = None) -> UIDirective:
    """Build UI directive for a specific field.
    
    Args:
        step: Current wizard step
        field_name: Field to build UI for
        current_values: Current blueprint values for pre-filling
        
    Returns:
        UIDirective for rendering the field
    """
    step_schema = get_step_schema(step)
    if not step_schema or field_name not in step_schema["fields"]:
        # Fallback for unknown field
        return UIDirective(
            type=UIComponentType.SHORT_TEXT,
            label=f"Enter {field_name}",
            field=field_name
        )
    
    field_def = step_schema["fields"][field_name]
    component_type = UIComponentType(field_def["type"])
    
    # Build options if present
    options = None
    if "options" in field_def:
        options = [UIOption(**opt) for opt in field_def["options"]]
    
    # Build constraints if present
    constraints = None
    if "constraints" in field_def:
        constraints = UIConstraints(**field_def["constraints"])
    
    return UIDirective(
        type=component_type,
        label=field_def["label"],
        field=field_name,
        options=options,
        constraints=constraints
    )


def get_next_required_field(step: WizardStep, current_values: Optional[Dict] = None) -> Optional[str]:
    """Get the next required field that needs to be filled.
    
    Args:
        step: Current wizard step
        current_values: Current blueprint values
        
    Returns:
        Field name or None if all required fields are filled
    """
    step_schema = get_step_schema(step)
    if not step_schema:
        return None
    
    current_values = current_values or {}
    
    for field_name, field_def in step_schema["fields"].items():
        if field_def.get("required", False):
            if field_name not in current_values or current_values[field_name] is None:
                return field_name
    
    return None


def get_all_required_fields(step: WizardStep) -> List[str]:
    """Get all required fields for a step.
    
    Args:
        step: Wizard step
        
    Returns:
        List of required field names
    """
    step_schema = get_step_schema(step)
    if not step_schema:
        return []
    
    return [
        field_name
        for field_name, field_def in step_schema["fields"].items()
        if field_def.get("required", False)
    ]


def build_assistant_message(step: WizardStep, field_name: str) -> str:
    """Build assistant message for a field.
    
    Args:
        step: Current wizard step
        field_name: Field being asked about
        
    Returns:
        Friendly assistant message
    """
    step_schema = get_step_schema(step)
    if not step_schema or field_name not in step_schema["fields"]:
        return "Proseguiamo..."
    
    # Return the label as the message (it's already user-friendly in Italian)
    return step_schema["fields"][field_name]["label"]


def build_review_ui() -> UIDirective:
    """Build UI directive for review step."""
    return UIDirective(
        type=UIComponentType.CONFIRMATION,
        label="Confermi le informazioni inserite? Puoi anche scegliere di modificare.",
        field="user_confirmation",
        options=[
            UIOption(id="confirm", label="Conferma"),
            UIOption(id="edit", label="Modifica")
        ]
    )
