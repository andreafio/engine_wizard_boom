"""
Orchestrator Service V2
Advanced orchestrator that integrates all wizard services for deterministic question flow
"""
from dataclasses import dataclass
from typing import Any, Dict, Optional, List, Tuple
from app.core.logging import get_logger
from app.services.field_extractor_service import FieldExtractorService
from app.services.clarifier_service import ClarifierService
from app.services.quality_critic_service import QualityCriticService
from app.services.blueprint_review_service import BlueprintReviewService
from app.services.strategic_profile_service import StrategicProfileService
from app.services.input_normalizer_service import InputNormalizerService
from app.services.orchestrator_utils import (
    pick_next_question,
    apply_answer,
    get_field_state,
    _build_clarifier_context,
    _apply_quality_hint,
    calculate_progress,
    _fallback_ui_when_no_question,
    _assistant_copy,
    QUESTION_BANK
)

logger = get_logger(__name__)


@dataclass
class TurnInput:
    """Input for a wizard turn"""
    session_id: str
    event_id: str
    ui_event: Optional[Dict[str, Any]] = None  # {type, field, value, ui_type}
    user_message: Optional[str] = None
    context: Dict[str, Any] = None


@dataclass
class TurnOutput:
    """Output from a wizard turn"""
    assistant_message: str
    wizard: Dict[str, Any]


class SessionStore:
    """Interface for session storage - implement with Redis/memory as needed"""

    async def get_session(self, session_id: str, tenant_id: str) -> Dict[str, Any]:
        """Get session data"""
        raise NotImplementedError

    async def put_session(self, session_id: str, tenant_id: str, session: Dict[str, Any]) -> None:
        """Store session data"""
        raise NotImplementedError

    async def get_idempotent(self, session_id: str, event_id: str) -> Optional[Dict[str, Any]]:
        """Get cached result for idempotency"""
        raise NotImplementedError

    async def put_idempotent(self, session_id: str, event_id: str, result: Any) -> None:
        """Cache result for idempotency"""
        raise NotImplementedError


class OrchestratorServiceV2:
    """
    Advanced orchestrator service that integrates all wizard services.

    Provides deterministic question flow with intelligent service integration:
    - Field extraction from free text
    - Clarification when needed
    - Quality assessment and follow-ups
    - Review phase before generation
    - Internal profile generation
    """

    def __init__(
        self,
        session_store: SessionStore,
        field_extractor_service: FieldExtractorService,
        clarifier_service: ClarifierService,
        quality_critic_service: QualityCriticService,
        blueprint_review_service: BlueprintReviewService,
        strategic_profile_service: StrategicProfileService,
        input_normalizer_service: Optional[InputNormalizerService] = None,
    ):
        self.session_store = session_store
        self.question_bank = QUESTION_BANK
        self.field_extractor = field_extractor_service
        self.clarifier = clarifier_service
        self.critic = quality_critic_service
        self.review_service = blueprint_review_service
        self.profile_service = strategic_profile_service
        self.normalizer = input_normalizer_service or InputNormalizerService()

    async def handle_turn(self, tenant_id: str, payload: TurnInput) -> TurnOutput:
        """
        Handle a wizard turn with intelligent service integration.

        Args:
            tenant_id: Tenant identifier
            payload: Turn input data

        Returns:
            Turn output with assistant message and wizard state
        """
        # 0) Idempotency check
        cached = await self.session_store.get_idempotent(payload.session_id, payload.event_id)
        if cached:
            return TurnOutput(**cached)

        # 1) Load session state
        session = await self.session_store.get_session(payload.session_id, tenant_id)
        blueprint = session.get("blueprint", {})
        current_section = session.get("current_section", "Context")

        events: List[Dict[str, str]] = []

        # 2) Determine current expected question (deterministic)
        current_section, current_q = pick_next_question(
            blueprint=blueprint,
            question_bank=self.question_bank,
            current_section=current_section
        )

        # 3) Apply user input
        if payload.ui_event:
            # 3a) UI-driven input (preferred)
            apply_answer(
                blueprint=blueprint,
                field=payload.ui_event["field"],
                value=payload.ui_event["value"],
                ui_type=payload.ui_event.get("ui_type", current_q.ui["type"] if current_q else "unknown"),
                source="user",
                evidence="",
                normalizer=self.normalizer,
                question_bank=self.question_bank
            )
            events.append({"type": "saved", "label": "Salvato ✓"})

        elif payload.user_message and current_q:
            # 3b) Free text fallback: extract to current field
            extraction = await self.field_extractor.extract_field(
                current_section=current_section,
                current_field=current_q.field,
                ui_type=current_q.ui["type"],
                options=current_q.ui.get("options", []),
                user_message=payload.user_message,
                blueprint_snippet=get_field_state(blueprint, current_q.field),
            )

            # If needs clarification -> ask clarifier immediately
            if extraction.get("needs_clarification"):
                clar = await self.clarifier.generate_clarifier(
                    current_field=current_q.field,
                    context=_build_clarifier_context(blueprint),
                    user_message=payload.user_message,
                )
                out = self._build_wizard_response(
                    blueprint=blueprint,
                    current_section=current_section,
                    ui=clar,
                    assistant_message="Mi serve un dettaglio per essere preciso.",
                    events=events,
                )
                await self.session_store.put_session(payload.session_id, tenant_id, session)
                await self.session_store.put_idempotent(payload.session_id, payload.event_id, out.__dict__)
                return out

            # Apply extracted value
            apply_answer(
                blueprint=blueprint,
                field=extraction["field"],
                value=extraction["value"],
                ui_type=current_q.ui["type"],
                source="user",
                evidence=extraction.get("evidence", ""),
                normalizer=self.normalizer,
                question_bank=self.question_bank
            )
            events.append({"type": "saved", "label": "Salvato ✓"})

            # Quality critic for follow-up hints
            critique = await self.critic.critique_answer(
                field=extraction["field"],
                value=extraction["value"],
                ui_type=current_q.ui["type"],
                section=current_section
            )
            _apply_quality_hint(blueprint, critique)

        # 4) Advance: re-run selector after applying answer
        next_section, next_q = pick_next_question(
            blueprint=blueprint,
            question_bank=self.question_bank,
            current_section=current_section
        )

        # 5) If reached Review section, build Review UI
        if next_section == "Review":
            review = await self.review_service.build_review(blueprint=blueprint)
            ui = {
                "type": "confirmation",
                "label": "Confermi i dettagli e vuoi generare il profilo interno?",
                "field": "review.user_confirmation",
                "options": [
                    {"id": "confirm", "label": "Sì, genera"},
                    {"id": "edit", "label": "No, modifica"}
                ],
                "review": review
            }
            assistant_message = "Siamo in review. Controlla il riepilogo e conferma."
            out = self._build_wizard_response(
                blueprint=blueprint,
                current_section="Review",
                ui=ui,
                assistant_message=assistant_message,
                events=events
            )
            session["current_section"] = "Review"
            session["blueprint"] = blueprint
            await self.session_store.put_session(payload.session_id, tenant_id, session)
            await self.session_store.put_idempotent(payload.session_id, payload.event_id, out.__dict__)
            return out

        # 6) Normal: ask next question
        ui = next_q.ui if next_q else _fallback_ui_when_no_question()
        assistant_message = _assistant_copy(next_section, ui.get("label", "Proseguiamo."))
        out = self._build_wizard_response(
            blueprint=blueprint,
            current_section=next_section,
            ui=ui,
            assistant_message=assistant_message,
            events=events
        )

        # 7) Persist state
        session["current_section"] = next_section
        session["blueprint"] = blueprint
        await self.session_store.put_session(payload.session_id, tenant_id, session)
        await self.session_store.put_idempotent(payload.session_id, payload.event_id, out.__dict__)
        return out

    async def handle_generate_internal(self, tenant_id: str, session_id: str, event_id: str) -> Dict[str, Any]:
        """
        Generate internal strategic profile.

        Args:
            tenant_id: Tenant identifier
            session_id: Session identifier
            event_id: Event identifier for idempotency

        Returns:
            Internal profile data
        """
        cached = await self.session_store.get_idempotent(session_id, event_id)
        if cached:
            return cached

        session = await self.session_store.get_session(session_id, tenant_id)
        blueprint = session.get("blueprint", {})

        # Generate internal profile
        internal_profile = await self.profile_service.generate_internal_profile(blueprint)

        await self.session_store.put_idempotent(session_id, event_id, internal_profile)
        return internal_profile

    def _build_wizard_response(
        self,
        blueprint: Dict[str, Any],
        current_section: str,
        ui: Dict[str, Any],
        assistant_message: str,
        events: List[Dict[str, str]]
    ) -> TurnOutput:
        """
        Build wizard response.

        Args:
            blueprint: Current blueprint
            current_section: Current section
            ui: UI configuration
            assistant_message: Assistant message
            events: Event list

        Returns:
            TurnOutput with wizard state
        """
        wizard = {
            "current_section": current_section,
            "progress": calculate_progress(blueprint),
            "blueprint": blueprint,
            "ui": ui,
            "validation": {"errors": []},
            "events": events
        }
        return TurnOutput(assistant_message=assistant_message, wizard=wizard)