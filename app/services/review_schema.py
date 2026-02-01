"""Pydantic schema for review output validation."""
from pydantic import BaseModel, Field
from typing import List


class ReviewSummary(BaseModel):
    """Blueprint review summary for user confirmation."""
    confirmed: List[str] = Field(
        default_factory=list,
        description="List of confirmed items (status=confirmed)"
    )
    to_confirm: List[str] = Field(
        default_factory=list,
        description="List of draft items that need confirmation (status=draft)"
    )


class ReviewOutput(BaseModel):
    """Complete review output structure."""
    review: ReviewSummary = Field(description="Review summary with confirmed and to_confirm lists")
    
    def has_items_to_confirm(self) -> bool:
        """Check if there are items that need user confirmation.
        
        Returns:
            True if to_confirm list is not empty
        """
        return len(self.review.to_confirm) > 0
    
    def is_ready_for_generation(self) -> bool:
        """Check if blueprint is ready for generation (no pending confirmations).
        
        Returns:
            True if all items are confirmed
        """
        return len(self.review.to_confirm) == 0
    
    def total_items(self) -> int:
        """Get total number of items in review.
        
        Returns:
            Total count of confirmed + to_confirm items
        """
        return len(self.review.confirmed) + len(self.review.to_confirm)
