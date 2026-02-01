"""
Tests for updated Quality Critic Service (rule-based)
"""
import pytest
from app.services.quality_critic_service import QualityCriticService, QualityCritique


class TestQualityCriticService:
    """Test cases for rule-based quality critic"""

    def setup_method(self):
        """Setup test instance"""
        self.critic = QualityCriticService()

    def test_empty_value_critique(self):
        """Test critique of empty/null values"""
        result = self.critic._rule_based_critique(
            field="context.industry",
            value=None,
            ui_type="short_text",
            section="Context"
        )

        assert result.quality_score == 0.0
        assert result.is_vague == True
        assert result.recommend_deep == True
        assert result.recommended_followup_field == "context.company_size"
        assert result.reason == "empty value"

    def test_single_select_critique(self):
        """Test critique of single select answers"""
        result = self.critic._rule_based_critique(
            field="context.industry",
            value="ecommerce",
            ui_type="single_select",
            section="Context"
        )

        assert result.quality_score == 0.9
        assert result.is_vague == False
        assert result.recommend_deep == False
        assert result.recommended_followup_field is None
        assert result.reason == "selection made"

    def test_generic_marketing_phrase(self):
        """Test strict scoring of generic marketing phrases"""
        result = self.critic._rule_based_critique(
            field="objective.primary_goal",
            value="grow my business",
            ui_type="short_text",
            section="Objective"
        )

        assert result.quality_score == 0.2
        assert result.is_vague == True
        assert result.recommend_deep == True
        assert result.reason == "generic marketing phrase"

    def test_too_brief_short_text(self):
        """Test scoring of very brief short text answers"""
        result = self.critic._rule_based_critique(
            field="context.industry",
            value="tech",
            ui_type="short_text",
            section="Context"
        )

        assert result.quality_score == 0.3
        assert result.is_vague == True
        assert result.recommend_deep == True
        assert result.reason == "too brief"

    def test_good_short_text_with_specificity(self):
        """Test scoring of good short text with specific details"""
        result = self.critic._rule_based_critique(
            field="context.industry",
            value="software development for healthcare",
            ui_type="short_text",
            section="Context"
        )

        assert result.quality_score == 0.8
        assert result.is_vague == False
        assert result.recommend_deep == False
        assert result.reason == "specific and concise"

    def test_insufficient_long_text(self):
        """Test scoring of insufficient long text"""
        result = self.critic._rule_based_critique(
            field="offer.differentiator",
            value="we are different",
            ui_type="long_text",
            section="Offer"
        )

        assert result.quality_score == 0.2
        assert result.is_vague == True
        assert result.recommend_deep == True
        assert result.reason == "insufficient detail"

    def test_good_long_text(self):
        """Test scoring of detailed long text"""
        result = self.critic._rule_based_critique(
            field="offer.differentiator",
            value="Our platform uses AI to automate customer service responses, reducing response time by 80% and improving customer satisfaction scores by 45% compared to traditional methods.",
            ui_type="long_text",
            section="Offer"
        )

        # This has 25 words and specific details, should be good
        assert result.quality_score == 0.9
        assert result.is_vague == False
        assert result.recommend_deep == False
        assert result.reason == "detailed and specific"

    def test_multi_select_critique(self):
        """Test critique of multi-select answers"""
        result = self.critic._rule_based_critique(
            field="channels.current",
            value=["email", "social", "seo"],
            ui_type="multi_select",
            section="Channels"
        )

        assert result.quality_score == 0.9
        assert result.is_vague == False
        assert result.recommend_deep == False
        assert result.reason == "selection made"

    def test_followup_field_mapping(self):
        """Test that appropriate follow-up fields are recommended"""
        # Test Context section follow-ups
        result = self.critic._rule_based_critique(
            field="context.industry",
            value="tech",
            ui_type="short_text",
            section="Context"
        )

        assert result.recommended_followup_field == "context.company_size"

        # Test Objective section follow-ups
        result = self.critic._rule_based_critique(
            field="objective.primary_goal",
            value="grow",
            ui_type="short_text",
            section="Objective"
        )

        assert result.recommended_followup_field == "objective.secondary_goals"

    def test_no_followup_when_score_good(self):
        """Test that no follow-up is recommended when score is good"""
        result = self.critic._rule_based_critique(
            field="context.industry",
            value="E-commerce platform for fashion retailers",
            ui_type="short_text",
            section="Context"
        )

        assert result.quality_score >= 0.5
        assert result.recommend_deep == False
        assert result.recommended_followup_field is None

    def test_budget_field_specificity(self):
        """Test budget field specificity detection"""
        result = self.critic._rule_based_critique(
            field="constraints.budget_range",
            value="We have $50,000 for marketing this quarter",
            ui_type="short_text",
            section="Constraints"
        )

        # Should detect budget-specific terms like "$", "budget", "quarter"
        assert result.quality_score == 0.8
        assert result.is_vague == False
        assert result.reason == "specific and concise"

    @pytest.mark.asyncio
    async def test_async_interface(self):
        """Test the async interface still works"""
        result = await self.critic.critique_answer(
            field="context.industry",
            value="software",
            ui_type="short_text",
            section="Context"
        )

        assert isinstance(result, QualityCritique)
        assert result.quality_score == 0.3  # "software" is 1 word, too brief
        assert result.is_vague == True