"""Pydantic schemas for LLM outputs validation."""
from pydantic import BaseModel, Field, conlist, field_validator
from typing import List


class Slide(BaseModel):
    """Single presentation slide."""
    title: str = Field(min_length=1, max_length=200, description="Slide title")
    bullets: conlist(str, min_length=3, max_length=5) = Field(description="3-5 bullet points per slide")
    
    @field_validator('bullets')
    @classmethod
    def validate_bullets(cls, v: List[str]) -> List[str]:
        """Validate and clean bullet points."""
        cleaned = []
        seen = set()
        
        for bullet in v:
            # Normalize whitespace
            b = " ".join(bullet.split())
            # Clamp to 140 chars
            b = b[:140].rstrip()
            
            # Skip empty or duplicates
            if not b or b.lower() in seen:
                continue
            
            seen.add(b.lower())
            cleaned.append(b)
        
        if len(cleaned) < 3:
            raise ValueError("At least 3 valid bullet points required per slide")
        
        return cleaned[:5]  # Max 5 bullets


class ReportSection(BaseModel):
    """Single report section."""
    title: str = Field(min_length=1, max_length=200, description="Section title")
    content: str = Field(min_length=10, description="Section content (minimum 10 chars)")


class GenerationOutput(BaseModel):
    """Complete generation output structure."""
    slides: conlist(Slide, min_length=6, max_length=8) = Field(description="6-8 presentation slides")
    report_sections: conlist(ReportSection, min_length=5, max_length=7) = Field(description="5-7 report sections")
    assumptions: List[str] = Field(default_factory=list, description="Explicit assumptions made during generation")
    next_steps: conlist(str, min_length=3, max_length=10) = Field(description="3-10 recommended next steps")
    
    @field_validator('assumptions')
    @classmethod
    def validate_assumptions_not_empty(cls, v: List[str], info) -> List[str]:
        """Ensure assumptions are present when metrics are missing."""
        # This will be enforced at service level when blueprint lacks metrics
        return v
