"""
Orchestrator Service V2 Utilities
Supporting functions for the advanced orchestrator service
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class Question:
    """Question structure for the wizard"""
    id: str
    field: str
    ui: Dict[str, Any]
    layer: str = "core"  # "core" or "deep"
    required: bool = True
    depends_on: Optional[List[str]] = None
    info_gain: float = 0.5
    effort: float = 0.3
    can_be_inferred: bool = False
    ask_if_confidence_below: float = 0.8


@dataclass
class Section:
    """Section structure with questions"""
    name: str
    questions: List[Question]
    required: bool = True


def load_question_bank() -> Dict[str, Section]:
    """
    Load question bank from JSON file.

    Returns:
        Dictionary of sections with their questions
    """
    question_bank_path = Path(__file__).parent.parent.parent / "question_bank_v1.json"

    try:
        with open(question_bank_path, 'r', encoding='utf-8') as f:
            questions_data = json.load(f)

        # Group questions by section
        sections = {}
        for q_data in questions_data:
            section_name = q_data["section"]
            if section_name not in sections:
                sections[section_name] = Section(name=section_name, questions=[])

            # Create Question object
            question = Question(
                id=q_data["id"],
                field=q_data["field"],
                ui=q_data["ui"],
                layer=q_data.get("layer", "core"),
                required=True,  # All questions in v1 are required
                depends_on=q_data.get("depends_on", []),
                info_gain=q_data.get("info_gain", 0.5),
                effort=q_data.get("effort", 0.3),
                can_be_inferred=q_data.get("can_be_inferred", False),
                ask_if_confidence_below=q_data.get("ask_if_confidence_below", 0.8)
            )

            sections[section_name].questions.append(question)

        logger.info(f"Loaded question bank with {len(sections)} sections and {len(questions_data)} questions")
        return sections

    except Exception as e:
        logger.error(f"Failed to load question bank: {e}")
        # Fallback to empty question bank
        return {}


# Load question bank at module level
QUESTION_BANK = load_question_bank()
def pick_next_question(
    blueprint: Dict[str, Any],
    question_bank: Dict[str, Section],
    current_section: str
) -> Tuple[str, Optional[Question]]:
    """
    Deterministically pick the next question based on blueprint completeness.

    Args:
        blueprint: Current blueprint state
        question_bank: Available questions by section
        current_section: Current section being worked on

    Returns:
        Tuple of (next_section, next_question)
    """
    # Define regular sections (excluding Review)
    regular_sections = [s for s in question_bank.keys() if s != "Review"]

    # Check if current section has unanswered questions
    if current_section in question_bank and current_section != "Review":
        section = question_bank[current_section]
        for question in section.questions:
            if not _is_field_answered(blueprint, question.field):
                return current_section, question

    # If we're in the last regular section and just completed a question there,
    # check if this section is now complete - if so, go to Review
    if current_section == regular_sections[-1]:  # Last regular section
        section = question_bank[current_section]
        section_complete = all(_is_field_answered(blueprint, q.field) for q in section.questions)
        if section_complete:
            return "Review", None

    # Check if all regular sections are complete
    all_regular_complete = True
    for section_name in regular_sections:
        if section_name in question_bank:
            section = question_bank[section_name]
            for question in section.questions:
                if not _is_field_answered(blueprint, question.field):
                    all_regular_complete = False
                    break
            if not all_regular_complete:
                break

    # If all regular sections complete, go to Review
    if all_regular_complete:
        return "Review", None

    # Move to next regular section
    try:
        current_idx = regular_sections.index(current_section)
        next_idx = current_idx + 1

        if next_idx < len(regular_sections):
            next_section_name = regular_sections[next_idx]

            # Find first unanswered question in next section
            next_section = question_bank[next_section_name]
            for question in next_section.questions:
                if not _is_field_answered(blueprint, question.field):
                    return next_section_name, question

            # If next section is complete, keep moving
            return pick_next_question(blueprint, question_bank, next_section_name)

    except ValueError:
        pass

    # Fallback: start from first regular section
    return pick_next_question(blueprint, question_bank, regular_sections[0])


def apply_answer(
    blueprint: Dict[str, Any],
    field: str,
    value: Any,
    ui_type: str,
    source: str = "user",
    evidence: str = "",
    normalizer: Optional[Any] = None,
    question_bank: Optional[Dict[str, Section]] = None
) -> None:
    """
    Apply an answer to the blueprint.

    Args:
        blueprint: Blueprint to update
        field: Field path (e.g., "context.industry")
        value: Answer value
        ui_type: UI component type
        source: Source of the answer
        evidence: Evidence or context for the answer
        normalizer: Optional input normalizer service
        question_bank: Optional question bank for option lookup
    """
    # Normalize value if normalizer is provided
    normalized_value = value
    normalized_ids = []
    normalization_notes = ""

    if normalizer and question_bank:
        # Find the question to get options
        options = []
        for section in question_bank.values():
            for q in section.questions:
                if q.field == field:
                    options = q.ui.get("options", [])
                    break
            if options:
                break

        # Normalize the input
        norm_result = normalizer.normalize({
            "field": field,
            "ui_type": ui_type,
            "options": options,
            "raw_value": value,
            "locale": "it-IT"
        })

        normalized_value = norm_result.get("normalized_value", value)
        normalized_ids = norm_result.get("normalized_ids", [])
        normalization_notes = norm_result.get("notes", "")

        logger.info("value_normalized", field=field, original=value, normalized=normalized_value, ids=normalized_ids, notes=normalization_notes)

    # Navigate/create nested structure
    keys = field.split('.')
    current = blueprint

    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]

    # Set the value
    final_key = keys[-1]
    current[final_key] = {
        "value": normalized_value,
        "normalized_ids": normalized_ids,
        "normalization_notes": normalization_notes,
        "ui_type": ui_type,
        "source": source,
        "evidence": evidence,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    logger.info("answer_applied", field=field, value=normalized_value, source=source)


def get_field_state(blueprint: Dict[str, Any], field: str) -> Dict[str, Any]:
    """
    Get the current state of a field in the blueprint.

    Args:
        blueprint: Blueprint data
        field: Field path

    Returns:
        Field state or empty dict
    """
    keys = field.split('.')
    current = blueprint

    try:
        for key in keys:
            current = current[key]
        return current
    except (KeyError, TypeError):
        return {}


def _is_field_answered(blueprint: Dict[str, Any], field: str) -> bool:
    """
    Check if a field has been answered.

    Args:
        blueprint: Blueprint data
        field: Field path

    Returns:
        True if field has a value
    """
    state = get_field_state(blueprint, field)
    # Multi-select fields store answers in normalized_ids (value stays None)
    return bool(state.get("value")) or bool(state.get("normalized_ids"))


def _build_clarifier_context(blueprint: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build minimal context for clarifier service.

    Args:
        blueprint: Blueprint data

    Returns:
        Context dict with relevant sections
    """
    ctx = {}
    for k in ["context", "objective", "offer", "audience"]:
        if k in blueprint:
            ctx[k] = blueprint[k]
    return ctx


def _apply_quality_hint(blueprint: Dict[str, Any], critique: Dict[str, Any]) -> None:
    """
    Apply quality critique hints to blueprint.

    Args:
        blueprint: Blueprint to update
        critique: Quality critique result
    """
    if critique.get("recommend_deep_followup"):
        # Set flag for deep question follow-up
        blueprint.setdefault("_flags", {})
        blueprint["_flags"][f"needs_deep:{critique.get('followup_field')}"] = True


def calculate_progress(blueprint: Dict[str, Any]) -> float:
    """
    Calculate completion progress of the blueprint.

    Args:
        blueprint: Blueprint data

    Returns:
        Progress percentage (0.0 to 1.0)
    """
    total_questions = sum(len(section.questions) for section in QUESTION_BANK.values())
    answered_questions = 0

    for section in QUESTION_BANK.values():
        for question in section.questions:
            if _is_field_answered(blueprint, question.field):
                answered_questions += 1

    return answered_questions / total_questions if total_questions > 0 else 0.0


def _fallback_ui_when_no_question() -> Dict[str, Any]:
    """
    Fallback UI when no question is available.

    Returns:
        Fallback UI configuration
    """
    return {
        "type": "short_text",
        "label": "Aggiungi un dettaglio utile",
        "field": "notes.misc",
        "options": []
    }


def _assistant_copy(section: str, label: str) -> str:
    """
    Generate assistant message based on section and question.

    Args:
        section: Current section
        label: Question label

    Returns:
        Assistant message
    """
    return f"Step: {section}. {label}"