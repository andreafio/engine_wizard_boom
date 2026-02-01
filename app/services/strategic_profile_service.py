"""
Strategic Profile Service
Generates internal strategic profiles for marketing/sales teams from blueprint data
"""
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from app.llm.provider import LLMProvider
from app.core.logging import get_logger

logger = get_logger(__name__)


class OpenQuestion(BaseModel):
    """Open question with context and priority"""
    question: str
    why_it_matters: str
    priority: int = Field(ge=1, le=8)


class RiskWatchout(BaseModel):
    """Risk or watchout with impact and mitigation"""
    risk: str
    impact: str = Field(pattern="^(high|medium|low)$")
    mitigation: str


class RecommendedAction(BaseModel):
    """Recommended action with priority, rationale, and owner hint"""
    priority: int = Field(ge=1, le=3)
    action: str
    why: str
    owner_hint: str = Field(pattern="^(Marketing|Sales|Ops)$")


class ActionPlanStep(BaseModel):
    """90-minute action plan step"""
    step: int = Field(ge=1, le=5)
    task: str
    output: str


class StrategicProfile(BaseModel):
    """Strategic profile output - V2 consulting-grade"""
    summary: str = Field(max_length=500)  # max 10 lines
    profile: Dict[str, Any] = Field(default_factory=dict)
    assumptions: List[str] = Field(default_factory=list)
    open_questions: List[OpenQuestion] = Field(default_factory=list, max_length=8)
    risks_watchouts: List[RiskWatchout] = Field(default_factory=list)
    recommended_actions: List[RecommendedAction] = Field(default_factory=list, max_length=3)
    action_plan_90min: List[ActionPlanStep] = Field(default_factory=list, min_length=3, max_length=5)
    confidence_map: Dict[str, List[str]] = Field(default_factory=lambda: {
        "high": [],
        "medium": [],
        "low": []
    })


class StrategicProfileService:
    """
    Service for generating internal strategic profiles from blueprint data.

    Creates operational strategic profiles for marketing/sales teams based on
    confirmed blueprint fields, identifying assumptions, open questions, and
    recommended actions.
    """

    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider

    async def generate_profile(self, blueprint: Dict[str, Any]) -> StrategicProfile:
        """
        Generate a strategic profile from blueprint data.

        Args:
            blueprint: Complete blueprint with all sections

        Returns:
            StrategicProfile with analysis and recommendations
        """
        logger.info("generating_strategic_profile", blueprint_keys=list(blueprint.keys()))

        # Build prompt for LLM
        prompt = self._build_profile_prompt(blueprint)

        try:
            # Get LLM response
            response = await self.llm.generate_json(
                prompt=prompt,
                system_prompt="You generate an INTERNAL strategic profile for a marketing/sales team. Blueprint-only. No invented metrics. Return JSON only."
            )

            # Apply guardrails BEFORE validation
            response = self._apply_guardrails_to_dict(response)

            # Validate and return
            result = StrategicProfile(**response)

            logger.info(
                "profile_generated",
                summary_length=len(result.summary),
                assumptions_count=len(result.assumptions),
                questions_count=len(result.open_questions),
                risks_count=len(result.risks_watchouts),
                actions_count=len(result.recommended_actions),
                action_plan_steps=len(result.action_plan_90min)
            )

            return result

        except Exception as e:
            logger.error("profile_generation_failed", error=str(e))

            # Return safe fallback
            return StrategicProfile(
                summary="Unable to generate strategic profile due to processing error.",
                profile={},
                assumptions=["Profile generation encountered an error"],
                open_questions=[OpenQuestion(
                    question="Please verify blueprint data and try again",
                    why_it_matters="System encountered a processing error",
                    priority=1
                )],
                risks_watchouts=[RiskWatchout(
                    risk="Profile generation failed",
                    impact="high",
                    mitigation="Review blueprint data and retry"
                )],
                recommended_actions=[],
                action_plan_90min=[
                    ActionPlanStep(step=1, task="Verify blueprint data", output="Clean blueprint JSON"),
                    ActionPlanStep(step=2, task="Check system logs", output="Error diagnostics"),
                    ActionPlanStep(step=3, task="Retry generation", output="Strategic profile")
                ],
                confidence_map={"high": [], "medium": [], "low": ["Profile generation"]}
            )

    def _build_profile_prompt(self, blueprint: Dict[str, Any]) -> str:
        """Build the strategic profile generation prompt"""

        # Format blueprint as JSON
        blueprint_json = self._format_blueprint_json(blueprint)

        prompt = f"""SYSTEM:
You generate an INTERNAL consulting-grade strategic profile for a marketing/sales team.
Blueprint-only. Deterministic truth rules.

INPUT JSON:
{blueprint_json}

TRUTH RULES (NON-NEGOTIABLE):
- Use ONLY fields with status="confirmed" as facts.
- Fields with status="draft" or "missing" must NEVER be stated as facts.
  They can appear ONLY as assumptions, open questions, risks, or watchouts.
- Never invent numbers, KPIs, budgets, targets, timelines, or performance results.
- If an item sounds like a fact but is not confirmed, reframe it as an assumption or question.

GOAL:
Produce a profile that an internal consultant can use immediately:
- Clear summary
- Structured profile sections
- Assumptions (explicit)
- Open questions (prioritized, with why_it_matters)
- Risks & watchouts (with mitigation)
- Recommended actions (prioritized, with owner_hint)
- 90-minute action plan (3–5 steps, concrete outputs)
- Confidence map

OUTPUT JSON ONLY (no markdown):
{{
  "summary": "max 10 lines",
  "profile": {{
    "context": {{}},
    "objective": {{}},
    "offer": {{}},
    "audience": {{}},
    "funnel": {{}},
    "channels": {{}},
    "assets_tracking": {{}},
    "constraints": {{}},
    "risks": {{}}
  }},
  "assumptions": ["..."],
  "open_questions": [
    {{"question": "...", "why_it_matters": "...", "priority": 1}}
  ],
  "risks_watchouts": [
    {{"risk": "...", "impact": "high|medium|low", "mitigation": "..."}}
  ],
  "recommended_actions": [
    {{"priority": 1, "action": "...", "why": "...", "owner_hint": "Marketing|Sales|Ops"}}
  ],
  "action_plan_90min": [
    {{"step": 1, "task": "...", "output": "..."}}
  ],
  "confidence_map": {{
    "high": ["..."],
    "medium": ["..."],
    "low": ["..."]
  }}
}}

STYLE:
- Operational, concise, no hype.
- Bullets should be short and executable.
- Prefer specifics derived from confirmed blueprint fields.
- If metrics are missing, include an assumption:
  "Mancano dati quantitativi (CPL, CAC, conversioni, ROI): le priorità sono qualitative."
Return JSON only.
"""
        return prompt

    def _apply_guardrails_to_dict(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply post-LLM guardrails to raw response before validation.

        Checks:
        - Open questions max 8, priorities 1..8, unique
        - Action plan 90min: 3-5 steps, each with concrete output
        """
        # Guardrail 1: Open questions max 8, priority 1..8, unique
        open_questions = response.get("open_questions", [])
        if len(open_questions) > 8:
            logger.warning("open_questions_exceeded", count=len(open_questions))
            open_questions = open_questions[:8]

        # Ensure priorities are sequential and unique
        for idx, question in enumerate(open_questions, start=1):
            if isinstance(question, dict):
                question["priority"] = idx

        response["open_questions"] = open_questions

        # Guardrail 2: Action plan 90min must have 3-5 steps with concrete outputs
        action_plan = response.get("action_plan_90min", [])
        
        if len(action_plan) < 3:
            logger.warning("action_plan_too_short", count=len(action_plan))
            # Add fallback steps
            while len(action_plan) < 3:
                step_num = len(action_plan) + 1
                action_plan.append({
                    "step": step_num,
                    "task": f"Review missing data for step {step_num}",
                    "output": "Data analysis document"
                })
        elif len(action_plan) > 5:
            logger.warning("action_plan_too_long", count=len(action_plan))
            action_plan = action_plan[:5]

        # Ensure step numbers are sequential
        for idx, step in enumerate(action_plan, start=1):
            if isinstance(step, dict):
                step["step"] = idx
                # Validate that each step has a concrete output
                if not step.get("output") or len(step["output"].strip()) < 5:
                    logger.warning("action_plan_step_missing_output", step=step["step"])
                    step["output"] = f"Deliverable for step {step['step']}"

        response["action_plan_90min"] = action_plan

        return response

    def _format_blueprint_json(self, blueprint: Dict[str, Any]) -> str:
        """Format blueprint as clean JSON string"""
        # Create a clean copy for JSON formatting
        clean_blueprint = {}

        for section, data in blueprint.items():
            if isinstance(data, dict):
                # Remove empty/null values for cleaner JSON
                clean_section = {k: v for k, v in data.items() if v not in (None, '', [], {})}
                if clean_section:
                    clean_blueprint[section] = clean_section
            elif data not in (None, '', [], {}):
                clean_blueprint[section] = data

        return f"""{{
  "blueprint": {clean_blueprint}
}}"""


# Convenience function
async def generate_strategic_profile(blueprint: Dict[str, Any]) -> StrategicProfile:
    """
    Generate a strategic profile from blueprint data

    Usage:
        profile = await generate_strategic_profile(blueprint_data)
    """
    from app.llm.openai_provider import OpenAIProvider
    import os

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    llm = OpenAIProvider(api_key=api_key, model="gpt-4o-mini")
    service = StrategicProfileService(llm)

    return await service.generate_profile(blueprint)


# Add method to StrategicProfileService class
async def generate_internal_profile(self, blueprint: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate internal profile in orchestrator format.

    Args:
        blueprint: Complete blueprint data

    Returns:
        Internal profile data with all V2 fields
    """
    profile_result = await self.generate_profile(blueprint)
    
    return {
        "summary": profile_result.summary,
        "profile": profile_result.profile,
        "assumptions": profile_result.assumptions,
        "open_questions": [
            {
                "question": q.question,
                "why_it_matters": q.why_it_matters,
                "priority": q.priority
            }
            for q in profile_result.open_questions
        ],
        "risks_watchouts": [
            {
                "risk": r.risk,
                "impact": r.impact,
                "mitigation": r.mitigation
            }
            for r in profile_result.risks_watchouts
        ],
        "recommended_actions": [
            {
                "priority": action.priority,
                "action": action.action,
                "why": action.why,
                "owner_hint": action.owner_hint
            }
            for action in profile_result.recommended_actions
        ],
        "action_plan_90min": [
            {
                "step": step.step,
                "task": step.task,
                "output": step.output
            }
            for step in profile_result.action_plan_90min
        ],
        "confidence_map": profile_result.confidence_map
    }

# Add the method to the class
StrategicProfileService.generate_internal_profile = generate_internal_profile