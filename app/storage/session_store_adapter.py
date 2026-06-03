"""
Adapter that bridges RedisStore (Session Pydantic) with OrchestratorServiceV2 SessionStore interface.

V2 uses Dict[str, Any] with shape:
  {"blueprint": {...}, "current_section": "Context", "tenant_id": "...", "session_id": "..."}

RedisStore uses Session Pydantic models.

This adapter translates between the two representations without modifying either side.
"""
from typing import Any, Dict, Optional

from app.services.orchestrator_service_v2 import SessionStore
from app.storage.redis_store import RedisStore
from app.wizard.schema import FieldStatus, WizardStep
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Maps V2 question_bank section names → V1 WizardStep values
# Verified against question_bank_v1.json sections:
# ['AssetsTracking', 'Audience', 'Channels', 'Constraints', 'Context',
#  'Funnel', 'Objective', 'Offer', 'Review', 'Risks']
_SECTION_TO_STEP: Dict[str, str] = {
    "Context":       "context",
    "Objective":     "objective",
    "Offer":         "value_prop",
    "Audience":      "target_market",
    "Funnel":        "channels_assets",
    "Channels":      "channels_assets",
    "AssetsTracking":"channels_assets",
    "Constraints":   "constraints",
    "Risks":         "constraints",
    "Review":        "review",
}

_STEP_TO_SECTION: Dict[str, str] = {
    "context":        "Context",
    "objective":      "Objective",
    "value_prop":     "Offer",
    "target_market":  "Audience",
    "channels_assets":"Channels",
    "constraints":    "Constraints",
    "review":         "Review",
    "completed":      "Review",
}


def _section_to_step(section: str) -> str:
    return _SECTION_TO_STEP.get(section, "context")


def _step_to_section(step_value: str) -> str:
    return _STEP_TO_SECTION.get(step_value, "Context")


def _pydantic_to_v2_blueprint(session) -> Dict[str, Any]:
    """
    Convert Session.blueprint (Pydantic) to V2 flat blueprint dict.

    V2 structure:
      blueprint["context"]["industry"] = {"value": "ecommerce", "source": "user", ...}

    Pydantic structure:
      session.blueprint.context.value = {"industry": "ecommerce", ...}
    """
    blueprint: Dict[str, Any] = {}
    section_map = {
        "context":        session.blueprint.context,
        "objective":      session.blueprint.objective,
        "target_market":  session.blueprint.target_market,
        "value_prop":     session.blueprint.value_prop,
        "channels_assets":session.blueprint.channels_assets,
        "constraints":    session.blueprint.constraints,
    }
    for section_name, section in section_map.items():
        if section.value and isinstance(section.value, dict):
            blueprint[section_name] = {}
            for field_name, field_value in section.value.items():
                # If already in V2 envelope format, keep it as-is
                if isinstance(field_value, dict) and "value" in field_value:
                    blueprint[section_name][field_name] = field_value
                else:
                    blueprint[section_name][field_name] = {
                        "value": field_value,
                        "source": "user",
                        "timestamp": "",
                        "ui_type": "unknown",
                        "evidence": "",
                        "normalized_ids": [],
                        "normalization_notes": "",
                    }
    return blueprint


def _apply_v2_blueprint_to_pydantic(v2_blueprint: Dict[str, Any], session) -> None:
    """
    Apply V2 blueprint changes back to the Pydantic Session.

    Extracts .value from each V2 field envelope and stores it in the
    appropriate BlueprintSection.value dict.
    """
    section_map = {
        "context":        session.blueprint.context,
        "objective":      session.blueprint.objective,
        "target_market":  session.blueprint.target_market,
        "value_prop":     session.blueprint.value_prop,
        "channels_assets":session.blueprint.channels_assets,
        "constraints":    session.blueprint.constraints,
    }
    for section_name, section in section_map.items():
        if section_name not in v2_blueprint:
            continue
        v2_section = v2_blueprint[section_name]
        current_values = section.value if isinstance(section.value, dict) else {}
        for field_name, field_envelope in v2_section.items():
            if isinstance(field_envelope, dict) and "value" in field_envelope:
                current_values[field_name] = field_envelope["value"]
            else:
                current_values[field_name] = field_envelope
        section.value = current_values
        section.status = FieldStatus.DRAFT


class RedisSessionStoreAdapter(SessionStore):
    """
    Adapts RedisStore to the SessionStore interface expected by OrchestratorServiceV2.

    Session dict format used internally by V2:
    {
        "session_id": str,
        "tenant_id": str,
        "blueprint": Dict,         # V2 nested dict with field envelopes
        "current_section": str,    # e.g. "Context", "Offer"
        "_pydantic_json": str,     # serialized Session Pydantic for round-trip
    }

    The full V2 blueprint is stored in a separate Redis key (v2_bp:{session_id})
    to survive round-trips without losing V2-only sections or normalized_ids.
    """

    def __init__(self, redis_store: RedisStore):
        self._store = redis_store

    def _v2_bp_key(self, session_id: str) -> str:
        return f"v2_bp:{session_id}"

    async def _load_v2_blueprint(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load the full V2 blueprint from its dedicated Redis/memory key."""
        import json
        key = self._v2_bp_key(session_id)
        if self._store.redis:
            data = await self._store.redis.get(key)
        else:
            data = self._store.memory_store.get(key)
        return json.loads(data) if data else None

    async def _save_v2_blueprint(self, session_id: str, blueprint: Dict[str, Any]) -> None:
        """Persist the full V2 blueprint to its dedicated Redis/memory key."""
        import json
        key = self._v2_bp_key(session_id)
        data = json.dumps(blueprint, default=str)
        if self._store.redis:
            await self._store.redis.setex(key, settings.session_ttl_seconds, data)
        else:
            self._store.memory_store[key] = data

    async def get_session(self, session_id: str, tenant_id: str) -> Dict[str, Any]:
        from app.wizard.state import Session  # avoid circular import
        session: Optional[Session] = await self._store.get_session(session_id)
        if not session:
            raise KeyError(f"Session not found: {session_id}")

        # Prefer the full V2 blueprint stored by a previous put_session.
        # Fall back to deriving it from the Pydantic model (first call).
        blueprint = await self._load_v2_blueprint(session_id)
        if blueprint is None:
            blueprint = _pydantic_to_v2_blueprint(session)

        current_section = _step_to_section(session.current_step.value)

        return {
            "session_id": session_id,
            "tenant_id": tenant_id,
            "blueprint": blueprint,
            "current_section": current_section,
            "_pydantic_json": session.model_dump_json(),
        }

    async def put_session(self, session_id: str, tenant_id: str, session_dict: Dict[str, Any]) -> None:
        from app.wizard.state import Session  # avoid circular import
        pydantic_json = session_dict.get("_pydantic_json")
        if not pydantic_json:
            logger.error("put_session_missing_pydantic_json", session_id=session_id)
            raise ValueError("Missing _pydantic_json in session dict")

        pydantic_session = Session.model_validate_json(pydantic_json)

        # Apply V2 blueprint changes back to the Pydantic model (best-effort for
        # sections that have a V1 counterpart; V2-only sections are kept in Redis).
        v2_blueprint = session_dict.get("blueprint", {})
        _apply_v2_blueprint_to_pydantic(v2_blueprint, pydantic_session)

        # Sync current step from V2 current_section
        new_section = session_dict.get("current_section", "Context")
        step_value = _section_to_step(new_section)
        try:
            pydantic_session.current_step = WizardStep(step_value)
        except ValueError:
            logger.warning("unknown_section_mapping",
                           section=new_section, fallback="context")

        # Keep _pydantic_json up-to-date for the next get_session call
        session_dict["_pydantic_json"] = pydantic_session.model_dump_json()

        # Persist the FULL V2 blueprint so no data is lost on the next get_session
        await self._save_v2_blueprint(session_id, v2_blueprint)

        await self._store.save_session(pydantic_session)

    async def get_idempotent(self, session_id: str, event_id: str) -> Optional[Dict[str, Any]]:
        return await self._store.get_idempotent(event_id)

    async def put_idempotent(self, session_id: str, event_id: str, result: Any) -> None:
        await self._store.put_idempotent(event_id, result)
