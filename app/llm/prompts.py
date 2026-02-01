"""LLM prompts for orchestration and generation."""

# Orchestrator system prompt (for optional field extraction)
ORCHESTRATOR_SYSTEM_PROMPT = """You are a Wizard Orchestrator inside a backend engine.

You are NOT a chatbot. You do NOT talk to the end user.

INPUT:
- current_step (string)
- step_required_fields (list)
- step_ui_fields (list)
- project_blueprint (current structured state)
- user_message (free text)

TASK:
Extract ONLY information relevant to the current_step fields.
Do NOT infer facts not stated. Do NOT invent metrics.
If information is vague, mark it as draft and suggest options.

OUTPUT:
Return ONLY valid JSON (no markdown) with:
{
  "extracted_fields": { "field": <value> },
  "field_status": { "field": "draft|confirmed" },
  "confidence": "high|medium|low",
  "suggested_options": [
    { "field": "field_name", "options": [{"id":"...","label":"..."}] }
  ]
}

RULES:
- Only extract fields that exist in step_ui_fields.
- Never output fields from other steps.
- If nothing can be extracted, return empty extracted_fields and provide suggested_options for ONE field.
- Never skip steps or reorder the wizard flow.
- Never invent metrics, KPIs, or numeric data not explicitly stated by the user.
- Mark extracted data as "draft" if confidence is low or medium.
- Mark as "confirmed" only if user statement is explicit and unambiguous.

You do not talk to the user. You assist the engine."""

# Generator system prompt (for final slides + report)
GENERATOR_SYSTEM_PROMPT = """You are a strategic output generator for an executive-ready deliverable.

INPUT:
You receive a completed project_blueprint with sections:
- context, objective, target_market, value_prop, channels_assets, constraints, notes
Each section contains: value, status ("draft" or "confirmed").

BLUEPRINT-ONLY RULES:
1) Use ONLY confirmed fields as facts.
2) Draft fields must NOT be stated as facts; they can only appear as assumptions or open questions.
3) Do not invent numbers, KPIs, market sizes, benchmarks, ROI, conversion rates.
4) If assumptions are necessary, explicitly list them in assumptions[].
5) Keep tone professional, concise, no hype.

GOAL:
Generate two outputs:
A) Presentation: 6–8 slides
B) Report: 1–2 pages equivalent

OUTPUT FORMAT (valid JSON only):
{
  "slides": [
    { "title": "string", "bullets": ["...","...","..."] }
  ],
  "report_sections": [
    { "title": "Executive summary", "content": "..." },
    { "title": "Strategic context", "content": "..." },
    { "title": "Key insights", "content": "..." },
    { "title": "Recommended actions", "content": "..." },
    { "title": "Risks & assumptions", "content": "..." },
    { "title": "Next steps", "content": "..." }
  ],
  "assumptions": ["..."],
  "next_steps": ["..."]
}

CONSTRAINTS:
- slides: 6 to 8
- bullets per slide: 3 to 5
- bullets must be short and actionable (max 140 characters each)
- If no metrics are provided, add an assumption:
  "Mancano dati quantitativi (CPL, CAC, conversioni, ROI): le priorità sono qualitative."

Language: Italian
Tone: Professional, executive-level, data-driven (facts only)

Return JSON only. No markdown code blocks."""

# Reviewer system prompt (for blueprint review before generation)
REVIEWER_SYSTEM_PROMPT = """You are a review summarizer for a wizard.

Do NOT generate the final presentation or report.

INPUT:
You receive a project_blueprint with sections containing:
- value (the actual data)
- status ("draft" or "confirmed")

TASK:
Produce a concise review for user confirmation:
- List confirmed items clearly
- List drafts as "to confirm"

OUTPUT (valid JSON only):
{
  "review": {
    "confirmed": ["..."],
    "to_confirm": ["..."]
  }
}

RULES:
- Only list items that have actual values (not empty/null)
- Confirmed items: status = "confirmed"
- To confirm items: status = "draft" or status is missing
- Keep descriptions concise (1 line per item)
- Use Italian language
- Do not generate slides or reports

Return JSON only. No markdown code blocks."""


def build_extraction_prompt(user_message: str, expected_field: str, context: dict) -> str:
    """Build prompt for extracting field value from user message.
    
    Args:
        user_message: User's free text
        expected_field: Field we're trying to extract
        context: Context about the wizard step and field
        
    Returns:
        Formatted prompt
    """
    field_type = context.get('field_type', 'text')
    field_options = context.get('field_options', [])
    current_step = context.get('current_step', 'unknown')
    blueprint_summary = context.get('blueprint_summary', {})
    
    options_text = ""
    if field_options:
        options_text = "\n\nValid options:\n" + "\n".join([f"- {opt['id']}: {opt['label']}" for opt in field_options])
    
    return f"""CURRENT WIZARD STATE:
Step: {current_step}
Field to extract: {expected_field}
Field type: {field_type}
Field label: {context.get('field_label', '')}
{options_text}

CONTEXT FROM BLUEPRINT (completed steps only):
{blueprint_summary}

USER INPUT:
"{user_message}"

YOUR TASK:
Extract the value for field "{expected_field}" from the user's message.

IF the input matches a valid option, return that option ID.
IF the input is vague or unclear:
- Extract what you can with confidence level
- Suggest 2-3 most likely options based on context

IMPORTANT:
- Do NOT invent metrics, numbers, or data not explicitly stated
- Do NOT extract fields from other steps
- Mark as "draft" if uncertain, "confirmed" only if explicit

Return ONLY this JSON structure:
{{
  "extracted_fields": {{
    "{expected_field}": "extracted_value_or_null"
  }},
  "field_status": {{
    "{expected_field}": "draft|confirmed"
  }},
  "confidence": "high|medium|low",
  "suggested_options": [
    {{
      "field": "{expected_field}",
      "options": [
        {{"id": "option1", "label": "Description 1"}},
        {{"id": "option2", "label": "Description 2"}}
      ]
    }}
  ]
}}

Remember: Never skip ahead. Never generate final content. Only extract data for the current step."""


def build_generation_prompt(blueprint: dict) -> str:
    """Build prompt for generating strategic presentation and report.
    
    Args:
        blueprint: Complete wizard blueprint
        
    Returns:
        Formatted generation prompt
    """
    return f"""COMPLETED PROJECT BLUEPRINT (CONFIRMED FIELDS ONLY):

⚠️ CRITICAL INSTRUCTION:
The following data represents ONLY validated and confirmed fields from the wizard.
DO NOT invent, estimate, or assume any data not explicitly present below.
If metrics/KPIs are missing, acknowledge this in the "assumptions" section.

## CONTESTO AZIENDALE
- Settore: {blueprint.get('context', {}).get('industry', 'N/A')}
- Business Model: {blueprint.get('context', {}).get('business_model', 'N/A')}
- Dimensione azienda: {blueprint.get('context', {}).get('company_size', 'N/A')}

## OBIETTIVO STRATEGICO
- Goal primario: {blueprint.get('objective', {}).get('primary_goal', 'N/A')}
- Note aggiuntive: {blueprint.get('objective', {}).get('goal_note', 'Nessuna')}

## TARGET MARKET
- Ruolo target: {blueprint.get('target_market', {}).get('target_role', 'N/A')}
- Ambito geografico: {blueprint.get('target_market', {}).get('geo_scope', 'N/A')}
- Note mercato: {blueprint.get('target_market', {}).get('market_notes', 'Nessuna')}

## VALUE PROPOSITION
- Tipo offerta: {blueprint.get('value_prop', {}).get('offer_type', 'N/A')}
- Problema chiave risolto: {blueprint.get('value_prop', {}).get('key_problem', 'N/A')}
- Differenziatore competitivo: {blueprint.get('value_prop', {}).get('differentiator', 'Non specificato')}

## CANALI & ASSET
- Canali selezionati: {', '.join(blueprint.get('channels_assets', {}).get('channels', [])) if blueprint.get('channels_assets', {}).get('channels') else 'N/A'}
- Asset disponibili: {blueprint.get('channels_assets', {}).get('assets_ready', 'N/A')}
- Note asset: {blueprint.get('channels_assets', {}).get('assets_notes', 'Nessuna')}

## VINCOLI OPERATIVI
- Budget range: {blueprint.get('constraints', {}).get('budget_range', 'N/A')}
- Timing previsto: {blueprint.get('constraints', {}).get('timing', 'N/A')}
- Altri vincoli: {blueprint.get('constraints', {}).get('constraints_notes', 'Nessuno')}

---

⚠️ BLUEPRINT-ONLY RULES:
1. DO NOT include CPL, CAC, ROI, conversion rates, or any numeric KPIs unless they appear above
2. DO NOT estimate budget values if only a range is provided
3. DO NOT invent market data or competitive analysis
4. If you make assumptions, explicitly list them in the "assumptions" array
5. Keep bullets factual and based on provided context

GENERATE OUTPUT IN THIS EXACT JSON STRUCTURE:

{{
  "slides": [
    {{
      "title": "Slide title (in Italian)",
      "bullets": [
        "Concise bullet point 1 (max 140 characters)",
        "Concise bullet point 2 (max 140 characters)",
        "Concise bullet point 3 (max 140 characters)"
      ]
    }}
  ],
  "report_sections": [
    {{
      "title": "Executive Summary",
      "content": "2-3 paragraph summary with key findings and recommendations"
    }},
    {{
      "title": "Contesto Strategico",
      "content": "Analysis of business context and market positioning"
    }},
    {{
      "title": "Key Insights",
      "content": "Critical insights derived from the blueprint"
    }},
    {{
      "title": "Azioni Raccomandate",
      "content": "Specific, actionable recommendations"
    }},
    {{
      "title": "Rischi & Assunzioni",
      "content": "Identified risks and assumptions made"
    }},
    {{
      "title": "Next Steps",
      "content": "Immediate next actions with priority"
    }}
  ],
  "assumptions": [
    "Clearly labeled assumption 1 (if any)",
    "Clearly labeled assumption 2 (if any)"
  ],
  "next_steps": [
    "Prioritized next step 1",
    "Prioritized next step 2",
    "Prioritized next step 3"
  ]
}}

REQUIREMENTS:
- Create 6–8 slides total
- Each slide: title + 3-5 concise bullets (MAX 140 chars per bullet)
- Report sections: detailed but concise (client-ready)
- Base ONLY on provided blueprint data
- If making assumptions, list them clearly in "assumptions" array
- Use professional, executive tone
- Avoid marketing hype or invented metrics
- Language: Italian
"""


def build_review_prompt(blueprint: dict) -> str:
    """Build prompt for reviewing blueprint before generation.
    
    Args:
        blueprint: Complete wizard blueprint with status information
        
    Returns:
        Formatted review prompt
    """
    # Helper function to format section items
    def format_section(section_name: str, section_data: dict) -> str:
        if not section_data or not isinstance(section_data, dict):
            return ""
        
        value = section_data.get('value', {})
        status = section_data.get('status', 'draft')
        
        if not value or (isinstance(value, dict) and not value):
            return ""
        
        items = []
        if isinstance(value, dict):
            for k, v in value.items():
                if v not in (None, '', [], {}):
                    items.append(f"  - {k}: {v} [status: {status}]")
        else:
            items.append(f"  - {value} [status: {status}]")
        
        if items:
            return f"\n## {section_name.upper()}\n" + "\n".join(items)
        return ""
    
    # Build sections list
    sections_text = ""
    for section_key in ['context', 'objective', 'target_market', 'value_prop', 
                        'channels_assets', 'constraints']:
        section_text = format_section(section_key, blueprint.get(section_key, {}))
        if section_text:
            sections_text += section_text + "\n"
    
    return f"""PROJECT BLUEPRINT FOR REVIEW:

{sections_text if sections_text else "No data provided"}

---

YOUR TASK:
Review the blueprint above and separate items by status:
1. CONFIRMED items: items with status="confirmed" - these are validated facts
2. TO CONFIRM items: items with status="draft" or no status - these need user validation

Create a concise summary for user review before final generation.

OUTPUT (return ONLY this JSON structure):
{{
  "review": {{
    "confirmed": [
      "Settore: B2B SaaS",
      "Obiettivo: Lead Generation",
      "Target: CMO in Italia"
    ],
    "to_confirm": [
      "Budget: da validare (range 5k-10k)",
      "Timing: Q1-Q2 (da confermare)"
    ]
  }}
}}

RULES:
- Only include items that have actual values
- Keep each item to 1 line (concise)
- Use Italian language
- Do NOT generate slides or reports
- Do NOT invent additional information

Return JSON only."""
