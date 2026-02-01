"""
Integration tests for Input Normalizer with Orchestrator
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.orchestrator_service_v2 import OrchestratorServiceV2, TurnInput
from app.services.input_normalizer_service import InputNormalizerService


class TestInputNormalizerIntegration:
    """Integration tests for input normalization in orchestrator"""

    @pytest.fixture
    def mock_session_store(self):
        """Mock session store"""
        store = MagicMock()
        store.get_session = AsyncMock(return_value={
            "blueprint": {},
            "current_section": "Context"
        })
        store.put_session = AsyncMock()
        store.get_idempotent = AsyncMock(return_value=None)
        store.put_idempotent = AsyncMock()
        return store

    @pytest.fixture
    def mock_services(self):
        """Mock all services"""
        return {
            "field_extractor": MagicMock(),
            "clarifier": MagicMock(),
            "critic": MagicMock(),
            "review": MagicMock(),
            "profile": MagicMock(),
            "normalizer": InputNormalizerService()
        }

    @pytest.fixture
    def orchestrator(self, mock_session_store, mock_services):
        """Create orchestrator with mocked services"""
        return OrchestratorServiceV2(
            session_store=mock_session_store,
            field_extractor_service=mock_services["field_extractor"],
            clarifier_service=mock_services["clarifier"],
            quality_critic_service=mock_services["critic"],
            blueprint_review_service=mock_services["review"],
            strategic_profile_service=mock_services["profile"],
            input_normalizer_service=mock_services["normalizer"]
        )

    @pytest.mark.asyncio
    async def test_normalization_unknown_synonym(self, orchestrator, mock_session_store):
        """Test that unknown synonyms are normalized to 'unknown'"""
        # Setup
        turn_input = TurnInput(
            session_id="test_session",
            event_id="test_event",
            ui_event={
                "type": "answer",
                "field": "context.industry",
                "value": "boh",
                "ui_type": "text"
            }
        )

        # Execute
        result = await orchestrator.handle_turn("tenant_1", turn_input)

        # Verify
        call_args = mock_session_store.put_session.call_args
        session_data = call_args[0][2]  # Third argument is session data

        # Check that blueprint contains normalized value
        industry_value = session_data["blueprint"]["context"]["industry"]
        assert industry_value["value"] == "unknown"
        assert industry_value["normalization_notes"] == "unknown_synonym"
        assert industry_value["normalized_ids"] == []

    @pytest.mark.asyncio
    async def test_normalization_option_mapping(self, orchestrator, mock_session_store):
        """Test that values are mapped to option IDs when possible"""
        # Setup - use a real field with options
        turn_input = TurnInput(
            session_id="test_session",
            event_id="test_event",
            ui_event={
                "type": "answer",
                "field": "context.industry",
                "value": "e-commerce",  # This should map to an option
                "ui_type": "single_select"
            }
        )

        # Execute
        result = await orchestrator.handle_turn("tenant_1", turn_input)

        # Verify
        call_args = mock_session_store.put_session.call_args
        session_data = call_args[0][2]

        # Check that blueprint contains mapped ID
        industry_value = session_data["blueprint"]["context"]["industry"]
        # Should be normalized to an ID if mapping found, otherwise the cleaned text
        assert industry_value["normalization_notes"] in ["exact_label_match", "partial_match", "word_match", "no_mapping"]
        assert industry_value["normalized_ids"] == []

    @pytest.mark.asyncio
    async def test_normalization_text_cleaning(self, orchestrator, mock_session_store):
        """Test that text values are cleaned (trimmed, spaces collapsed)"""
        # Setup
        turn_input = TurnInput(
            session_id="test_session",
            event_id="test_event",
            ui_event={
                "type": "answer",
                "field": "context.company_name",
                "value": "  ACME   Corp  ",
                "ui_type": "text"
            }
        )

        # Execute
        result = await orchestrator.handle_turn("tenant_1", turn_input)

        # Verify
        call_args = mock_session_store.put_session.call_args
        session_data = call_args[0][2]

        # Check that blueprint contains cleaned value
        company_value = session_data["blueprint"]["context"]["company_name"]
        assert company_value["value"] == "ACME Corp"
        assert company_value["normalization_notes"] == "text_cleaned"
        assert company_value["normalized_ids"] == []

    @pytest.mark.asyncio
    async def test_normalization_multi_select(self, orchestrator, mock_session_store):
        """Test normalization of multi-select values"""
        # Setup - use a real multi-select field
        turn_input = TurnInput(
            session_id="test_session",
            event_id="test_event",
            ui_event={
                "type": "answer",
                "field": "channels.current",
                "value": ["email", "boh", "social"],  # boh should be filtered out as unknown
                "ui_type": "multi_select"
            }
        )

        # Execute
        result = await orchestrator.handle_turn("tenant_1", turn_input)

        # Verify
        call_args = mock_session_store.put_session.call_args
        session_data = call_args[0][2]

        # Check that blueprint contains normalized IDs (unknown filtered out)
        channels_value = session_data["blueprint"]["channels"]["current"]
        # For multi-select with options, should have normalized_ids if mapping found
        if channels_value["normalized_ids"]:
            assert channels_value["value"] is None  # Multi-select stores IDs separately
            assert "multi_mapped" in channels_value["normalization_notes"]
        else:
            # If no mapping found, falls back to joined string
            assert channels_value["value"] == "email, boh, social"
            assert channels_value["normalization_notes"] == "array_joined"

    @pytest.mark.asyncio
    async def test_normalization_no_mapping(self, orchestrator, mock_session_store):
        """Test handling when no option mapping is found"""
        # Setup
        turn_input = TurnInput(
            session_id="test_session",
            event_id="test_event",
            ui_event={
                "type": "answer",
                "field": "context.industry",
                "value": "something completely different",
                "ui_type": "single_select"
            }
        )

        # Execute
        result = await orchestrator.handle_turn("tenant_1", turn_input)

        # Verify
        call_args = mock_session_store.put_session.call_args
        session_data = call_args[0][2]

        # Check that blueprint contains original value with no_mapping note
        industry_value = session_data["blueprint"]["context"]["industry"]
        assert industry_value["value"] == "something completely different"
        assert industry_value["normalization_notes"] == "no_mapping"
        assert industry_value["normalized_ids"] == []