"""
Input Normalizer Service
Normalizes raw user input values for blueprint storage
"""
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class NormalizationInput:
    """Input for normalization"""
    field: str
    ui_type: str
    options: List[Dict[str, str]]
    raw_value: Any
    locale: str = "it-IT"


@dataclass
class NormalizationOutput:
    """Output of normalization"""
    field: str
    normalized_value: Optional[str]
    normalized_ids: List[str]
    is_unknown: bool
    notes: str


class InputNormalizerService:
    """
    Service for normalizing user input values before blueprint storage.
    Handles text cleaning, synonym mapping, and option id mapping.
    """

    # Synonyms that map to "unknown"
    UNKNOWN_SYNONYMS = {
        "boh", "non so", "n/a", "na", "non lo so", "non ne ho idea",
        "non saprei", "nessuna idea", "non ho idea", "non so dire",
        "non specificato", "non definito", "non applicabile", "n.d.",
        "tbd", "to be defined", "da definire", "?", "??", "???",
        "non ricordo", "non mi viene in mente", "non ho pensato",
        "non ho deciso", "non ho scelto", "non ho selezionato"
    }

    def __init__(self):
        self.logger = logger

    def normalize(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a single field value.

        Args:
            input_data: Dict with field, ui_type, options, raw_value, locale

        Returns:
            Dict with normalized_value, normalized_ids, is_unknown, notes
        """
        try:
            # Parse input
            norm_input = NormalizationInput(
                field=input_data["field"],
                ui_type=input_data["ui_type"],
                options=input_data.get("options", []),
                raw_value=input_data["raw_value"],
                locale=input_data.get("locale", "it-IT")
            )

            # Normalize
            result = self._normalize_value(norm_input)

            # Return as dict
            return {
                "field": result.field,
                "normalized_value": result.normalized_value,
                "normalized_ids": result.normalized_ids,
                "is_unknown": result.is_unknown,
                "notes": result.notes
            }

        except Exception as e:
            self.logger.error(f"Normalization failed for field {input_data.get('field', 'unknown')}: {e}")
            return {
                "field": input_data.get("field", "unknown"),
                "normalized_value": None,
                "normalized_ids": [],
                "is_unknown": False,
                "notes": f"normalization_error: {str(e)}"
            }

    def _normalize_value(self, input_data: NormalizationInput) -> NormalizationOutput:
        """
        Core normalization logic.
        """
        raw_value = input_data.raw_value

        # Handle None/empty values
        if raw_value is None or raw_value == "":
            return NormalizationOutput(
                field=input_data.field,
                normalized_value=None,
                normalized_ids=[],
                is_unknown=False,
                notes="empty_value"
            )

        # Clean text for string inputs
        if isinstance(raw_value, str):
            cleaned_value = self._clean_text(raw_value)

            # Check for unknown synonyms
            if self._is_unknown_synonym(cleaned_value):
                return NormalizationOutput(
                    field=input_data.field,
                    normalized_value="unknown",
                    normalized_ids=[],
                    is_unknown=True,
                    notes="unknown_synonym"
                )

            # Try to map to options if available
            if input_data.options:
                mapped_ids, mapping_notes = self._map_to_option_ids(cleaned_value, input_data.options)

                if input_data.ui_type == "multi_select":
                    # For multi-select, return the mapped ids
                    return NormalizationOutput(
                        field=input_data.field,
                        normalized_value=cleaned_value if not mapped_ids else None,
                        normalized_ids=mapped_ids,
                        is_unknown=False,
                        notes=mapping_notes
                    )
                else:
                    # For single select, if we found a mapping, use the id as normalized_value
                    if mapped_ids:
                        return NormalizationOutput(
                            field=input_data.field,
                            normalized_value=mapped_ids[0],  # Single id
                            normalized_ids=[],
                            is_unknown=False,
                            notes=mapping_notes
                        )
                    else:
                        # No mapping found for single select with options
                        return NormalizationOutput(
                            field=input_data.field,
                            normalized_value=cleaned_value,
                            normalized_ids=[],
                            is_unknown=False,
                            notes="no_mapping"
                        )

            # No options, return cleaned text
            return NormalizationOutput(
                field=input_data.field,
                normalized_value=cleaned_value,
                normalized_ids=[],
                is_unknown=False,
                notes="text_cleaned"
            )

        # Handle array inputs (multi-select)
        elif isinstance(raw_value, list):
            if input_data.ui_type == "multi_select" and input_data.options:
                # Try to map each item to option ids
                all_ids = []
                notes_parts = []

                for item in raw_value:
                    if isinstance(item, str):
                        item_cleaned = self._clean_text(item)
                        if self._is_unknown_synonym(item_cleaned):
                            continue  # Skip unknown items
                        item_ids, item_notes = self._map_to_option_ids(item_cleaned, input_data.options)
                        all_ids.extend(item_ids)
                        if item_notes != "no_mapping":
                            notes_parts.append(item_notes)

                # Remove duplicates
                all_ids = list(dict.fromkeys(all_ids))

                notes = "multi_mapped" if notes_parts else "multi_no_mapping"

                return NormalizationOutput(
                    field=input_data.field,
                    normalized_value=None,
                    normalized_ids=all_ids,
                    is_unknown=False,
                    notes=notes
                )

            # Fallback: join array into string
            joined = ", ".join(str(x) for x in raw_value)
            cleaned = self._clean_text(joined)
            return NormalizationOutput(
                field=input_data.field,
                normalized_value=cleaned,
                normalized_ids=[],
                is_unknown=False,
                notes="array_joined"
            )

        # Handle other types (numbers, booleans, etc.)
        else:
            str_value = str(raw_value)
            cleaned = self._clean_text(str_value)
            return NormalizationOutput(
                field=input_data.field,
                normalized_value=cleaned,
                normalized_ids=[],
                is_unknown=False,
                notes="type_converted"
            )

    def _clean_text(self, text: str) -> str:
        """
        Clean text: trim whitespace, collapse multiple spaces.
        """
        if not text:
            return ""

        # Trim whitespace
        cleaned = text.strip()

        # Collapse multiple spaces/tabs/newlines
        cleaned = re.sub(r'\s+', ' ', cleaned)

        return cleaned

    def _is_unknown_synonym(self, text: str) -> bool:
        """
        Check if text is an unknown synonym.
        """
        if not text:
            return False

        text_lower = text.lower().strip()
        return text_lower in self.UNKNOWN_SYNONYMS

    def _map_to_option_ids(self, text: str, options: List[Dict[str, str]]) -> Tuple[List[str], str]:
        """
        Try to map text to option ids.

        Returns:
            Tuple of (matched_ids, notes)
        """
        if not text or not options:
            return [], "no_options"

        text_lower = text.lower().strip()
        matched_ids = []

        # Try exact match on label first (more user-friendly)
        for option in options:
            label = option.get("label", "").lower()
            if label == text_lower:
                matched_ids.append(option["id"])
                break

        if matched_ids:
            return matched_ids, "exact_label_match"

        # Try exact match on id
        for option in options:
            option_id = option.get("id", "").lower()
            if option_id == text_lower:
                matched_ids.append(option["id"])
                break

        if matched_ids:
            return matched_ids, "exact_id_match"

        # Try partial/fuzzy match on label
        for option in options:
            label = option.get("label", "").lower()
            if text_lower in label or label in text_lower:
                matched_ids.append(option["id"])

        if matched_ids:
            return matched_ids, "partial_match"

        # Try word-based matching (any word from text matches any word in label)
        text_words = set(text_lower.split())
        for option in options:
            label = option.get("label", "").lower()
            label_words = set(label.split())
            if text_words & label_words:  # Intersection
                matched_ids.append(option["id"])

        if matched_ids:
            return matched_ids, "word_match"

        return [], "no_mapping"