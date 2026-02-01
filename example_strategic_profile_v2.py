"""
Example: Strategic Profile V2 Output
Consulting-grade internal profile generation
"""

example_blueprint = {
    "context": {
        "industry": "Software Development",
        "company_size": "50-100 employees",
        "description": "B2B SaaS company providing project management tools"
    },
    "objective": {
        "goal": "Increase market share by 15% in 12 months",
        "timeline": "Q4 2026",
        "budget": "50000"
    },
    "offer": {
        "value_prop": "Streamlined project management with AI insights",
        "pricing": "Subscription-based"
    },
    "audience": {
        "target_audience": ["Small to medium businesses", "Tech startups"],
        "persona": "Technical project managers"
    },
    "funnel": {},  # Missing
    "channels": {
        "primary": ["LinkedIn", "Google Ads"]
    },
    "assets_tracking": {},  # Missing
    "constraints": {
        "limitations": "Limited marketing team bandwidth"
    },
    "risks": {}  # Missing
}

# Expected V2 Output:
expected_v2_output = {
    "summary": """
B2B SaaS company (50-100 employees) in software development, targeting SMBs and tech startups 
with AI-powered project management tools. Goal: 15% market share growth in 12 months with $50K budget.
Primary channels: LinkedIn, Google Ads. Team constraint: limited marketing bandwidth.

CONFIRMED: Context, objectives, offer basics, audience, channels
DRAFT/MISSING: Funnel conversion stages, tracking KPIs, risk assessment

Next priorities: Define funnel metrics, establish KPI tracking, complete competitive analysis.
""",
    "profile": {
        "context": {
            "industry": "Software Development",
            "size": "50-100 employees",
            "type": "B2B SaaS",
            "product": "Project management with AI insights"
        },
        "objective": {
            "goal": "15% market share increase",
            "timeline": "12 months (Q4 2026)",
            "budget": "$50,000",
            "target_type": "Market share growth"
        },
        "offer": {
            "value_proposition": "AI-powered project management",
            "pricing_model": "Subscription-based",
            "differentiation": "AI insights (to be detailed)"
        },
        "audience": {
            "segments": ["SMBs", "Tech startups"],
            "primary_persona": "Technical project managers",
            "company_size": "Mid-market focus"
        },
        "funnel": {
            "status": "undefined",
            "note": "Conversion stages and metrics not specified"
        },
        "channels": {
            "primary": ["LinkedIn", "Google Ads"],
            "strategy": "To be defined"
        },
        "assets_tracking": {
            "status": "missing",
            "note": "No KPIs or tracking metrics specified"
        },
        "constraints": {
            "team": "Limited marketing bandwidth",
            "budget": "$50K for 12 months",
            "implications": "Must prioritize high-ROI activities"
        },
        "risks": {
            "status": "not assessed",
            "note": "Competitive and market risks not documented"
        }
    },
    "assumptions": [
        "Current market share percentage is unknown (baseline needed for 15% growth target)",
        "Competitor landscape not analyzed yet (positioning strategy depends on this)",
        "CAC, LTV, and conversion metrics unavailable (ROI calculation not possible)",
        "LinkedIn and Google Ads chosen without channel effectiveness data",
        "Mancano dati quantitativi (CPL, CAC, conversioni, ROI): le priorità sono qualitative"
    ],
    "open_questions": [
        {
            "question": "What is the current market share percentage?",
            "why_it_matters": "Need baseline to measure 15% growth target progress",
            "priority": 1
        },
        {
            "question": "What are current CAC and LTV metrics?",
            "why_it_matters": "Critical for ROI calculation and budget allocation",
            "priority": 2
        },
        {
            "question": "How many active users/customers currently?",
            "why_it_matters": "Baseline for growth measurement and conversion tracking",
            "priority": 3
        },
        {
            "question": "What are typical funnel conversion rates in your industry?",
            "why_it_matters": "Need benchmarks to set realistic conversion goals",
            "priority": 4
        },
        {
            "question": "Who are the top 5 direct competitors?",
            "why_it_matters": "Positioning strategy requires competitive analysis",
            "priority": 5
        },
        {
            "question": "What specific AI features differentiate your product?",
            "why_it_matters": "Core to value proposition and messaging",
            "priority": 6
        },
        {
            "question": "What content themes resonate with technical PMs?",
            "why_it_matters": "LinkedIn strategy requires relevant content planning",
            "priority": 7
        },
        {
            "question": "What is the sales team size and capacity?",
            "why_it_matters": "Funnel design depends on sales resources available",
            "priority": 8
        }
    ],
    "risks_watchouts": [
        {
            "risk": "Undefined funnel conversion metrics",
            "impact": "high",
            "mitigation": "Define conversion goals for each stage (awareness → decision) within 2 weeks"
        },
        {
            "risk": "No tracking KPIs established",
            "impact": "high",
            "mitigation": "Set up analytics tracking for CAC, LTV, conversion rate immediately"
        },
        {
            "risk": "Limited marketing bandwidth with ambitious 15% growth goal",
            "impact": "medium",
            "mitigation": "Focus on 2 primary channels (LinkedIn, Google Ads) with clear ROI targets"
        },
        {
            "risk": "No competitive positioning defined",
            "impact": "medium",
            "mitigation": "Complete competitor analysis to identify differentiation opportunities"
        },
        {
            "risk": "Budget allocation unclear across channels",
            "impact": "medium",
            "mitigation": "Split $50K budget based on expected CAC and conversion data from test campaigns"
        }
    ],
    "recommended_actions": [
        {
            "priority": 1,
            "action": "Define funnel conversion metrics and tracking setup",
            "why": "Cannot measure 15% growth without baseline metrics and conversion tracking",
            "owner_hint": "Ops"
        },
        {
            "priority": 2,
            "action": "Complete competitive analysis for top 5 direct competitors",
            "why": "Positioning strategy requires understanding competitive landscape",
            "owner_hint": "Marketing"
        },
        {
            "priority": 3,
            "action": "Develop LinkedIn content strategy for technical PM audience",
            "why": "Primary channel needs content plan aligned with persona interests",
            "owner_hint": "Marketing"
        }
    ],
    "action_plan_90min": [
        {
            "step": 1,
            "task": "List current known metrics (users, revenue, leads) to establish baseline",
            "output": "Baseline metrics spreadsheet with gaps identified"
        },
        {
            "step": 2,
            "task": "Research and list top 5-7 direct competitors with basic positioning notes",
            "output": "Competitive landscape doc with positioning matrix"
        },
        {
            "step": 3,
            "task": "Draft 10 LinkedIn post ideas targeting technical project managers",
            "output": "Content themes list with engagement hooks"
        },
        {
            "step": 4,
            "task": "Define 3-4 key funnel stages with draft conversion goal percentages",
            "output": "Funnel stage definitions with target conversion rates"
        },
        {
            "step": 5,
            "task": "Set up Google Analytics goals for primary conversion events",
            "output": "Analytics tracking configuration document"
        }
    ],
    "confidence_map": {
        "high": [
            "context.industry",
            "context.company_size",
            "objective.budget",
            "objective.timeline",
            "channels.primary"
        ],
        "medium": [
            "context.description",
            "objective.goal",
            "offer.value_prop",
            "offer.pricing",
            "audience.target_audience",
            "audience.persona",
            "constraints.limitations"
        ],
        "low": [
            "funnel (completely missing)",
            "assets_tracking (no KPIs defined)",
            "risks (not assessed)",
            "offer.differentiation (vague)",
            "audience.sizing (unknown)",
            "channels.strategy (undefined)"
        ]
    }
}

print(f"""
Strategic Profile V2 Example
============================

Blueprint Input: {len(example_blueprint)} sections
- Confirmed: context, objective, offer, audience, channels, constraints
- Missing: funnel, assets_tracking, risks

Expected Output:
- Summary: {len(expected_v2_output['summary'])} characters
- Profile sections: {len(expected_v2_output['profile'])} sections
- Assumptions: {len(expected_v2_output['assumptions'])} items
- Open questions: {len(expected_v2_output['open_questions'])} questions (max 8)
- Risks & watchouts: {len(expected_v2_output['risks_watchouts'])} risks
- Recommended actions: {len(expected_v2_output['recommended_actions'])} actions
- 90-min action plan: {len(expected_v2_output['action_plan_90min'])} steps (3-5)
- Confidence map: high={len(expected_v2_output['confidence_map']['high'])}, medium={len(expected_v2_output['confidence_map']['medium'])}, low={len(expected_v2_output['confidence_map']['low'])}
""")
