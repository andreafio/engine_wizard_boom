"""
Tests for Input Normalizer Service
"""
import pytest
from app.services.input_normalizer_service import InputNormalizerService


class TestInputNormalizerService:
    """Test cases for input normalization"""

    def setup_method(self):
        """Setup test instance"""
        self.normalizer = InputNormalizerService()

    def test_clean_text(self):
        """Test text cleaning functionality"""
        # Basic cleaning
        assert self.normalizer._clean_text("  hello world  ") == "hello world"
        assert self.normalizer._clean_text("hello\t\nworld") == "hello world"
        assert self.normalizer._clean_text("hello   world") == "hello world"

        # Empty/null handling
        assert self.normalizer._clean_text("") == ""
        assert self.normalizer._clean_text(None) == ""

    def test_unknown_synonyms(self):
        """Test unknown synonym detection"""
        # Known synonyms
        assert self.normalizer._is_unknown_synonym("boh") == True
        assert self.normalizer._is_unknown_synonym("non so") == True
        assert self.normalizer._is_unknown_synonym("n/a") == True
        assert self.normalizer._is_unknown_synonym("NON LO SO") == True  # Case insensitive

        # Not synonyms
        assert self.normalizer._is_unknown_synonym("marketing") == False
        assert self.normalizer._is_unknown_synonym("e-commerce") == False
        assert self.normalizer._is_unknown_synonym("") == False

    def test_normalize_empty_values(self):
        """Test normalization of empty/null values"""
        result = self.normalizer.normalize({
            "field": "test.field",
            "ui_type": "text",
            "options": [],
            "raw_value": None
        })

        assert result["normalized_value"] is None
        assert result["normalized_ids"] == []
        assert result["is_unknown"] == False
        assert result["notes"] == "empty_value"

    def test_normalize_unknown_synonyms(self):
        """Test normalization of unknown synonyms"""
        result = self.normalizer.normalize({
            "field": "test.field",
            "ui_type": "text",
            "options": [],
            "raw_value": "boh"
        })

        assert result["normalized_value"] == "unknown"
        assert result["normalized_ids"] == []
        assert result["is_unknown"] == True
        assert result["notes"] == "unknown_synonym"

    def test_normalize_text_without_options(self):
        """Test normalization of text without options"""
        result = self.normalizer.normalize({
            "field": "test.field",
            "ui_type": "text",
            "options": [],
            "raw_value": "  hello world  "
        })

        assert result["normalized_value"] == "hello world"
        assert result["normalized_ids"] == []
        assert result["is_unknown"] == False
        assert result["notes"] == "text_cleaned"

    def test_normalize_single_select_exact_match(self):
        """Test normalization with exact option match"""
        options = [
            {"id": "b2b", "label": "B2B"},
            {"id": "b2c", "label": "B2C"},
            {"id": "b2b2c", "label": "B2B2C"}
        ]

        result = self.normalizer.normalize({
            "field": "context.target_audience",
            "ui_type": "single_select",
            "options": options,
            "raw_value": "B2B"
        })

        assert result["normalized_value"] == "b2b"
        assert result["normalized_ids"] == []
        assert result["is_unknown"] == False
        assert result["notes"] == "exact_label_match"

    def test_normalize_single_select_partial_match(self):
        """Test normalization with partial option match"""
        options = [
            {"id": "digital_marketing", "label": "Digital Marketing"},
            {"id": "content_marketing", "label": "Content Marketing"}
        ]

        result = self.normalizer.normalize({
            "field": "context.industry",
            "ui_type": "single_select",
            "options": options,
            "raw_value": "digital"
        })

        assert result["normalized_value"] == "digital_marketing"
        assert result["normalized_ids"] == []
        assert result["is_unknown"] == False
        assert result["notes"] == "partial_match"

    def test_normalize_multi_select(self):
        """Test normalization for multi-select fields"""
        options = [
            {"id": "email", "label": "Email Marketing"},
            {"id": "social", "label": "Social Media"},
            {"id": "seo", "label": "SEO"}
        ]

        result = self.normalizer.normalize({
            "field": "channels.primary",
            "ui_type": "multi_select",
            "options": options,
            "raw_value": ["email", "social"]
        })

        assert result["normalized_value"] is None
        assert result["normalized_ids"] == ["email", "social"]
        assert result["is_unknown"] == False
        assert result["notes"] == "multi_mapped"

    def test_normalize_multi_select_with_unknown(self):
        """Test multi-select with unknown values filtered out"""
        options = [
            {"id": "email", "label": "Email Marketing"},
            {"id": "social", "label": "Social Media"}
        ]

        result = self.normalizer.normalize({
            "field": "channels.primary",
            "ui_type": "multi_select",
            "options": options,
            "raw_value": ["email", "boh", "social"]
        })

        assert result["normalized_value"] is None
        assert result["normalized_ids"] == ["email", "social"]
        assert result["is_unknown"] == False
        assert result["notes"] == "multi_mapped"

    def test_normalize_array_fallback(self):
        """Test array fallback to joined string"""
        result = self.normalizer.normalize({
            "field": "test.field",
            "ui_type": "text",  # Not multi_select
            "options": [],
            "raw_value": ["item1", "item2"]
        })

        assert result["normalized_value"] == "item1, item2"
        assert result["normalized_ids"] == []
        assert result["is_unknown"] == False
        assert result["notes"] == "array_joined"

    def test_normalize_numeric_value(self):
        """Test normalization of numeric values"""
        result = self.normalizer.normalize({
            "field": "metrics.budget",
            "ui_type": "number",
            "options": [],
            "raw_value": 50000
        })

        assert result["normalized_value"] == "50000"
        assert result["normalized_ids"] == []
        assert result["is_unknown"] == False
        assert result["notes"] == "type_converted"

    def test_normalize_boolean_value(self):
        """Test normalization of boolean values"""
        result = self.normalizer.normalize({
            "field": "context.has_website",
            "ui_type": "boolean",
            "options": [],
            "raw_value": True
        })

        assert result["normalized_value"] == "True"
        assert result["normalized_ids"] == []
        assert result["is_unknown"] == False
        assert result["notes"] == "type_converted"

    def test_normalize_word_matching(self):
        """Test word-based matching for options"""
        options = [
            {"id": "ecommerce_platform", "label": "E-commerce Platform"},
            {"id": "marketplace", "label": "Marketplace"}
        ]

        result = self.normalizer.normalize({
            "field": "context.business_type",
            "ui_type": "single_select",
            "options": options,
            "raw_value": "vendo su una piattaforma e-commerce"
        })

        assert result["normalized_value"] == "ecommerce_platform"
        assert result["normalized_ids"] == []
        assert result["is_unknown"] == False
        assert result["notes"] == "word_match"

    def test_normalize_no_mapping(self):
        """Test when no option mapping is found"""
        options = [
            {"id": "b2b", "label": "B2B"},
            {"id": "b2c", "label": "B2C"}
        ]

        result = self.normalizer.normalize({
            "field": "context.target",
            "ui_type": "single_select",
            "options": options,
            "raw_value": "completely different value"
        })

        assert result["normalized_value"] == "completely different value"
        assert result["normalized_ids"] == []
        assert result["is_unknown"] == False
        assert result["notes"] == "no_mapping"