"""Wizard schema definition and Pydantic models."""
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field
from enum import Enum


class FieldStatus(str, Enum):
    """Status of a blueprint field."""
    DRAFT = "draft"
    CONFIRMED = "confirmed"


class WizardStep(str, Enum):
    """Wizard steps in order."""
    CONTEXT = "context"
    OBJECTIVE = "objective"
    TARGET_MARKET = "target_market"
    VALUE_PROP = "value_prop"
    CHANNELS_ASSETS = "channels_assets"
    CONSTRAINTS = "constraints"
    REVIEW = "review"
    COMPLETED = "completed"


class UIComponentType(str, Enum):
    """UI component types."""
    SINGLE_SELECT = "single_select"
    MULTI_SELECT = "multi_select"
    SHORT_TEXT = "short_text"
    LONG_TEXT = "long_text"
    CONFIRMATION = "confirmation"
    SLIDER = "slider"


class UIOption(BaseModel):
    """Option for select components."""
    id: str
    label: str


class UIConstraints(BaseModel):
    """Constraints for UI components."""
    min: Optional[int] = None
    max: Optional[int] = None
    placeholder: Optional[str] = None


class UIDirective(BaseModel):
    """UI rendering directive."""
    type: UIComponentType
    label: str
    field: str
    options: Optional[List[UIOption]] = None
    constraints: Optional[UIConstraints] = None


class BlueprintSection(BaseModel):
    """A section of the wizard blueprint."""
    value: Optional[Dict[str, Any] | str] = None
    status: FieldStatus = FieldStatus.DRAFT


class Blueprint(BaseModel):
    """Complete wizard blueprint."""
    context: BlueprintSection = Field(default_factory=BlueprintSection)
    objective: BlueprintSection = Field(default_factory=BlueprintSection)
    target_market: BlueprintSection = Field(default_factory=BlueprintSection)
    value_prop: BlueprintSection = Field(default_factory=BlueprintSection)
    channels_assets: BlueprintSection = Field(default_factory=BlueprintSection)
    constraints: BlueprintSection = Field(default_factory=BlueprintSection)


class ValidationResult(BaseModel):
    """Validation result."""
    required_fields: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class WizardEvent(BaseModel):
    """Wizard UI event."""
    type: str
    label: str


class WizardState(BaseModel):
    """Current wizard state returned to frontend."""
    wizard_id: str = "strategic_snapshot_v1"
    current_step: WizardStep
    progress: float
    blueprint: Blueprint
    ui: UIDirective
    validation: ValidationResult = Field(default_factory=ValidationResult)
    events: List[WizardEvent] = Field(default_factory=list)


# Wizard Schema Definition
WIZARD_SCHEMA = {
    "wizard_id": "strategic_snapshot_v1",
    "steps": [
        {
            "step": WizardStep.CONTEXT,
            "order": 1,
            "fields": {
                "industry": {
                    "type": "single_select",
                    "label": "In che settore opera la tua azienda?",
                    "required": True,
                    "options": [
                        {"id": "ecommerce", "label": "E-commerce"},
                        {"id": "b2b_services", "label": "Servizi B2B"},
                        {"id": "saas", "label": "SaaS/Software"},
                        {"id": "retail", "label": "Retail/GDO"},
                        {"id": "manufacturing", "label": "Manifattura"},
                        {"id": "professional", "label": "Servizi professionali"},
                        {"id": "other", "label": "Altro"}
                    ]
                },
                "business_model": {
                    "type": "single_select",
                    "label": "Qual è il tuo modello di business principale?",
                    "required": True,
                    "options": [
                        {"id": "b2b", "label": "B2B"},
                        {"id": "b2c", "label": "B2C"},
                        {"id": "b2b2c", "label": "B2B2C"},
                        {"id": "marketplace", "label": "Marketplace"}
                    ]
                },
                "company_size": {
                    "type": "single_select",
                    "label": "Dimensione dell'azienda?",
                    "required": True,
                    "options": [
                        {"id": "micro", "label": "Micro (1-10)"},
                        {"id": "small", "label": "Piccola (11-50)"},
                        {"id": "medium", "label": "Media (51-250)"},
                        {"id": "large", "label": "Grande (250+)"}
                    ]
                }
            }
        },
        {
            "step": WizardStep.OBJECTIVE,
            "order": 2,
            "fields": {
                "primary_goal": {
                    "type": "single_select",
                    "label": "Qual è il tuo obiettivo principale?",
                    "required": True,
                    "options": [
                        {"id": "leads", "label": "Generare nuovi lead"},
                        {"id": "sales", "label": "Aumentare le vendite"},
                        {"id": "awareness", "label": "Aumentare brand awareness"},
                        {"id": "retention", "label": "Migliorare retention clienti"},
                        {"id": "launch", "label": "Lanciare un prodotto"}
                    ]
                },
                "goal_note": {
                    "type": "long_text",
                    "label": "Note aggiuntive sull'obiettivo (opzionale)",
                    "required": False,
                    "constraints": {"placeholder": "Es: vogliamo raddoppiare i lead B2B in 6 mesi"}
                }
            }
        },
        {
            "step": WizardStep.TARGET_MARKET,
            "order": 3,
            "fields": {
                "target_role": {
                    "type": "single_select",
                    "label": "Chi è il tuo target principale?",
                    "required": True,
                    "options": [
                        {"id": "cxo", "label": "C-Level / Owner"},
                        {"id": "manager", "label": "Manager / Responsabili"},
                        {"id": "specialist", "label": "Specialist / Tecnici"},
                        {"id": "consumer", "label": "Consumatore finale"},
                        {"id": "mixed", "label": "Pubblico misto"}
                    ]
                },
                "geo_scope": {
                    "type": "single_select",
                    "label": "Ambito geografico?",
                    "required": True,
                    "options": [
                        {"id": "local", "label": "Locale (città/provincia)"},
                        {"id": "regional", "label": "Regionale"},
                        {"id": "national", "label": "Nazionale (Italia)"},
                        {"id": "international", "label": "Internazionale"}
                    ]
                },
                "market_notes": {
                    "type": "long_text",
                    "label": "Note aggiuntive sul target (opzionale)",
                    "required": False,
                    "constraints": {"placeholder": "Es: PMI nel settore manifatturiero del Nord Italia"}
                }
            }
        },
        {
            "step": WizardStep.VALUE_PROP,
            "order": 4,
            "fields": {
                "offer_type": {
                    "type": "single_select",
                    "label": "Cosa offri principalmente?",
                    "required": True,
                    "options": [
                        {"id": "product", "label": "Prodotto fisico"},
                        {"id": "service", "label": "Servizio"},
                        {"id": "software", "label": "Software/Piattaforma"},
                        {"id": "content", "label": "Contenuti/Formazione"},
                        {"id": "hybrid", "label": "Ibrido"}
                    ]
                },
                "key_problem": {
                    "type": "long_text",
                    "label": "Quale problema risolvi per il cliente?",
                    "required": True,
                    "constraints": {"placeholder": "Descrivi il pain point principale"}
                },
                "differentiator": {
                    "type": "long_text",
                    "label": "Qual è il tuo differenziatore chiave? (opzionale)",
                    "required": False,
                    "constraints": {"placeholder": "Cosa ti rende unico rispetto ai competitor"}
                }
            }
        },
        {
            "step": WizardStep.CHANNELS_ASSETS,
            "order": 5,
            "fields": {
                "channels": {
                    "type": "multi_select",
                    "label": "Quali canali vuoi usare? (min 1, max 4)",
                    "required": True,
                    "constraints": {"min": 1, "max": 4},
                    "options": [
                        {"id": "paid_search", "label": "Google Ads (Search)"},
                        {"id": "paid_social", "label": "Social Ads (FB/IG/LI)"},
                        {"id": "email", "label": "Email Marketing"},
                        {"id": "seo", "label": "SEO/Content"},
                        {"id": "linkedin_organic", "label": "LinkedIn Organico"},
                        {"id": "display", "label": "Display/Programmatic"},
                        {"id": "other", "label": "Altri canali"}
                    ]
                },
                "assets_ready": {
                    "type": "single_select",
                    "label": "Hai già materiali creativi pronti?",
                    "required": True,
                    "options": [
                        {"id": "yes_full", "label": "Sì, completi"},
                        {"id": "yes_partial", "label": "Sì, parziali"},
                        {"id": "no", "label": "No, da creare"}
                    ]
                },
                "assets_notes": {
                    "type": "long_text",
                    "label": "Note su asset e creatività (opzionale)",
                    "required": False,
                    "constraints": {"placeholder": "Es: abbiamo logo e foto prodotto"}
                }
            }
        },
        {
            "step": WizardStep.CONSTRAINTS,
            "order": 6,
            "fields": {
                "budget_range": {
                    "type": "single_select",
                    "label": "Budget mensile per il marketing?",
                    "required": True,
                    "options": [
                        {"id": "under_1k", "label": "< 1.000€"},
                        {"id": "1k_5k", "label": "1.000€ - 5.000€"},
                        {"id": "5k_10k", "label": "5.000€ - 10.000€"},
                        {"id": "10k_25k", "label": "10.000€ - 25.000€"},
                        {"id": "over_25k", "label": "> 25.000€"}
                    ]
                },
                "timing": {
                    "type": "single_select",
                    "label": "Quando vuoi iniziare?",
                    "required": True,
                    "options": [
                        {"id": "immediate", "label": "Subito (entro 2 settimane)"},
                        {"id": "one_month", "label": "Entro 1 mese"},
                        {"id": "quarter", "label": "Entro 3 mesi"},
                        {"id": "flexible", "label": "Flessibile"}
                    ]
                },
                "constraints_notes": {
                    "type": "long_text",
                    "label": "Altri vincoli o requisiti? (opzionale)",
                    "required": False,
                    "constraints": {"placeholder": "Es: stagionalità, scadenze specifiche, limitazioni"}
                }
            }
        },
        {
            "step": WizardStep.REVIEW,
            "order": 7,
            "fields": {
                "user_confirmation": {
                    "type": "confirmation",
                    "label": "Confermi le informazioni inserite?",
                    "required": True
                }
            }
        }
    ]
}


def get_step_schema(step: WizardStep) -> Optional[Dict]:
    """Get schema for a specific step."""
    for step_schema in WIZARD_SCHEMA["steps"]:
        if step_schema["step"] == step:
            return step_schema
    return None


def get_next_step(current_step: WizardStep) -> Optional[WizardStep]:
    """Get the next step in the wizard flow."""
    steps = [s["step"] for s in WIZARD_SCHEMA["steps"]]
    try:
        current_index = steps.index(current_step)
        if current_index < len(steps) - 1:
            return steps[current_index + 1]
        return WizardStep.COMPLETED
    except ValueError:
        return None


def calculate_progress(current_step: WizardStep) -> float:
    """Calculate progress percentage based on current step."""
    steps = [s["step"] for s in WIZARD_SCHEMA["steps"]]
    try:
        current_index = steps.index(current_step)
        return round((current_index / len(steps)) * 100, 1)
    except ValueError:
        return 0.0
