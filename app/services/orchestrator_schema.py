"""Pydantic schema for orchestrator output validation."""
from pydantic import BaseModel, Field
from typing import Dict, List, Literal, Optional


class SuggestedOption(BaseModel):
    """Single suggested option for a field."""
    id: str = Field(description="Option identifier")
    label: str = Field(description="Human-readable option label")


class FieldSuggestions(BaseModel):
    """Suggestions for a specific field."""
    field: str = Field(description="Field name")
    options: List[SuggestedOption] = Field(min_length=1, max_length=3, description="2-3 suggested options")


class OrchestratorOutput(BaseModel):
    """Validated orchestrator extraction output."""
    extracted_fields: Dict[str, Optional[str]] = Field(
        default_factory=dict,
        description="Extracted field values (field_name -> value)"
    )
    field_status: Dict[str, Literal["draft", "confirmed"]] = Field(
        default_factory=dict,
        description="Status of each extracted field"
    )
    confidence: Literal["high", "medium", "low"] = Field(
        description="Overall extraction confidence"
    )
    suggested_options: List[FieldSuggestions] = Field(
        default_factory=list,
        description="Suggested options when extraction is unclear"
    )
    
    def is_confirmed(self, field_name: str) -> bool:
        """Check if a field is confirmed (not draft).
        
        Args:
            field_name: Field to check
            
        Returns:
            True if field is confirmed
        """
        return self.field_status.get(field_name) == "confirmed"
    
    def get_value(self, field_name: str) -> Optional[str]:
        """Get extracted value for a field.
        
        Args:
            field_name: Field name
            
        Returns:
            Extracted value or None
        """
        return self.extracted_fields.get(field_name)
