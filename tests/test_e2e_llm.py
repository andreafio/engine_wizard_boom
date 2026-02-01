"""End-to-end integration tests with real LLM providers.

These tests make actual API calls to LLM providers and show real output.
Run with: pytest tests/test_e2e_llm.py -v -s --api-key=<YOUR_KEY>
"""
import pytest
import os
from app.services.orchestrator_service import OrchestratorService
from app.services.review_service import ReviewService
from app.services.generation_service import GenerationService
from app.llm.provider import ProviderFactory
from app.wizard.state import Session
from app.wizard.schema import Blueprint, BlueprintSection, WizardStep, FieldStatus


# Skip if no API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
skip_if_no_key = pytest.mark.skipif(
    not OPENAI_API_KEY,
    reason="No OPENAI_API_KEY found in environment"
)


@pytest.fixture
def real_llm():
    """Real LLM provider (OpenAI)."""
    if not OPENAI_API_KEY:
        pytest.skip("No OPENAI_API_KEY found")
    return ProviderFactory.create("openai", OPENAI_API_KEY, "gpt-4o-mini")


@pytest.fixture
def sample_session_minimal():
    """Minimal session for orchestrator testing."""
    session = Session(
        session_id="e2e-test-001",
        tenant_id="test-tenant",
        current_step=WizardStep.CONTEXT
    )
    return session


@pytest.fixture
def sample_session_complete():
    """Complete session for generation testing."""
    session = Session(
        session_id="e2e-test-002",
        tenant_id="test-tenant",
        current_step=WizardStep.REVIEW
    )
    
    # Build complete blueprint
    session.blueprint.context = BlueprintSection(
        value={
            "industry": "B2B SaaS",
            "business_model": "Subscription",
            "company_size": "Startup (10-50 dipendenti)"
        },
        status=FieldStatus.CONFIRMED
    )
    
    session.blueprint.objective = BlueprintSection(
        value={
            "primary_goal": "Lead Generation",
            "goal_note": "Obiettivo: generare 100 lead qualificati al mese"
        },
        status=FieldStatus.CONFIRMED
    )
    
    session.blueprint.target_market = BlueprintSection(
        value={
            "target_role": "Marketing Manager",
            "geo_scope": "Italia",
            "market_notes": "Focus su aziende B2B nel settore tech"
        },
        status=FieldStatus.CONFIRMED
    )
    
    session.blueprint.value_prop = BlueprintSection(
        value={
            "offer_type": "Piattaforma Software",
            "key_problem": "Automazione processi marketing manuali",
            "differentiator": "AI-powered automation + analytics integrati"
        },
        status=FieldStatus.CONFIRMED
    )
    
    session.blueprint.channels_assets = BlueprintSection(
        value={
            "channels": ["LinkedIn", "Google Ads", "Content Marketing"],
            "assets_ready": "Sito web, landing pages, case studies"
        },
        status=FieldStatus.CONFIRMED
    )
    
    session.blueprint.constraints = BlueprintSection(
        value={
            "budget_range": "5000-10000 euro/mese",
            "timing": "Q1 2026 (Gennaio-Marzo)",
            "constraints_notes": "Team marketing interno: 2 persone"
        },
        status=FieldStatus.CONFIRMED
    )
    
    return session


@skip_if_no_key
@pytest.mark.asyncio
async def test_orchestrator_real_extraction(real_llm, sample_session_minimal):
    """Test orchestrator with real LLM - explicit input."""
    print("\n" + "="*80)
    print("TEST: Orchestrator - Explicit Value Extraction")
    print("="*80)
    
    service = OrchestratorService(real_llm)
    
    user_message = "Siamo una startup B2B SaaS nel settore HR tech"
    expected_field = "industry"
    
    print(f"\n📥 USER INPUT: {user_message}")
    print(f"🎯 EXPECTED FIELD: {expected_field}")
    
    result = await service.extract_field(
        user_message=user_message,
        session=sample_session_minimal,
        expected_field=expected_field
    )
    
    print(f"\n📤 LLM OUTPUT:")
    print(f"  Extracted Fields: {result.get('extracted_fields', {})}")
    print(f"  Field Status: {result.get('field_status', {})}")
    print(f"  Confidence: {result.get('confidence', 'unknown')}")
    
    if result.get('suggested_options'):
        print(f"  Suggested Options: {result['suggested_options']}")
    
    # Assertions
    assert "industry" in result["extracted_fields"]
    assert result["confidence"] in ["high", "medium", "low"]
    assert "industry" in result["field_status"]
    
    print("\n✅ Test passed!")


@skip_if_no_key
@pytest.mark.asyncio
async def test_orchestrator_real_vague_input(real_llm, sample_session_minimal):
    """Test orchestrator with real LLM - vague input."""
    print("\n" + "="*80)
    print("TEST: Orchestrator - Vague Input with Suggestions")
    print("="*80)
    
    service = OrchestratorService(real_llm)
    
    user_message = "Vogliamo crescere nel mercato italiano"
    expected_field = "industry"
    
    print(f"\n📥 USER INPUT: {user_message}")
    print(f"🎯 EXPECTED FIELD: {expected_field}")
    
    result = await service.extract_field(
        user_message=user_message,
        session=sample_session_minimal,
        expected_field=expected_field
    )
    
    print(f"\n📤 LLM OUTPUT:")
    print(f"  Extracted Fields: {result.get('extracted_fields', {})}")
    print(f"  Field Status: {result.get('field_status', {})}")
    print(f"  Confidence: {result.get('confidence', 'unknown')}")
    
    if result.get('suggested_options'):
        print(f"\n  💡 Suggested Options:")
        for suggestion in result['suggested_options']:
            print(f"    Field: {suggestion.get('field')}")
            for opt in suggestion.get('options', []):
                print(f"      - {opt.get('id')}: {opt.get('label')}")
    
    # Vague input should have low confidence or suggestions
    assert result["confidence"] in ["low", "medium"] or len(result.get("suggested_options", [])) > 0
    
    print("\n✅ Test passed!")


@skip_if_no_key
@pytest.mark.asyncio
async def test_review_real_output(real_llm, sample_session_complete):
    """Test review service with real LLM."""
    print("\n" + "="*80)
    print("TEST: Review Service - Blueprint Review")
    print("="*80)
    
    service = ReviewService(real_llm)
    
    print("\n📋 BLUEPRINT TO REVIEW:")
    print(f"  Context: {sample_session_complete.blueprint.context.value}")
    print(f"  Objective: {sample_session_complete.blueprint.objective.value}")
    print(f"  Target: {sample_session_complete.blueprint.target_market.value}")
    
    result = await service.review_blueprint(sample_session_complete)
    
    print(f"\n📤 REVIEW OUTPUT:")
    print(f"\n✅ CONFIRMED ITEMS ({len(result['review']['confirmed'])}):")
    for item in result['review']['confirmed']:
        print(f"  • {item}")
    
    if result['review']['to_confirm']:
        print(f"\n⚠️  TO CONFIRM ({len(result['review']['to_confirm'])}):")
        for item in result['review']['to_confirm']:
            print(f"  • {item}")
    else:
        print(f"\n✅ All items confirmed - ready for generation!")
    
    # Assertions
    assert "review" in result
    assert "confirmed" in result["review"]
    assert len(result["review"]["confirmed"]) > 0
    
    print("\n✅ Test passed!")


@skip_if_no_key
@pytest.mark.asyncio
async def test_generator_real_output(real_llm, sample_session_complete):
    """Test generator with real LLM - full output."""
    print("\n" + "="*80)
    print("TEST: Generator - Complete Presentation & Report")
    print("="*80)
    
    service = GenerationService(real_llm)
    
    print("\n📋 BLUEPRINT INPUT:")
    print(f"  Industry: B2B SaaS")
    print(f"  Goal: Lead Generation (100/month)")
    print(f"  Target: Marketing Managers in Italia")
    print(f"  Channels: LinkedIn, Google Ads, Content")
    print(f"  Budget: 5k-10k/month")
    
    result = await service.generate_output(sample_session_complete)
    
    print(f"\n📤 GENERATED OUTPUT:")
    print(f"\n📊 PRESENTATION ({len(result['slides'])} slides):")
    for i, slide in enumerate(result['slides'], 1):
        print(f"\n  Slide {i}: {slide['title']}")
        for bullet in slide['bullets']:
            print(f"    • {bullet}")
    
    print(f"\n📄 REPORT ({len(result['report_sections'])} sections):")
    for section in result['report_sections']:
        print(f"\n  [{section['title']}]")
        # Show first 150 chars of content
        content = section['content']
        preview = content[:150] + "..." if len(content) > 150 else content
        print(f"  {preview}")
    
    if result.get('assumptions'):
        print(f"\n⚠️  ASSUMPTIONS ({len(result['assumptions'])}):")
        for assumption in result['assumptions']:
            print(f"  • {assumption}")
    
    print(f"\n🎯 NEXT STEPS ({len(result['next_steps'])}):")
    for step in result['next_steps']:
        print(f"  • {step}")
    
    # Assertions
    assert len(result['slides']) >= 6
    assert len(result['slides']) <= 8
    assert len(result['report_sections']) >= 5
    assert len(result['next_steps']) >= 3
    
    print("\n✅ Test passed!")


@skip_if_no_key
@pytest.mark.asyncio
async def test_full_workflow_e2e(real_llm):
    """Test complete workflow: orchestrator → review → generation."""
    print("\n" + "="*80)
    print("TEST: Full End-to-End Workflow")
    print("="*80)
    
    # Step 1: Create session
    session = Session(
        session_id="e2e-full-workflow",
        tenant_id="test-tenant",
        current_step=WizardStep.CONTEXT
    )
    
    # Step 2: Orchestrator extracts context
    print("\n📍 STEP 1: Orchestrator - Extract Context")
    orchestrator = OrchestratorService(real_llm)
    
    extract_result = await orchestrator.extract_field(
        user_message="Siamo una startup e-commerce di moda sostenibile in Italia",
        session=session,
        expected_field="industry"
    )
    
    print(f"  Extracted: {extract_result['extracted_fields']}")
    
    # Update blueprint
    session.blueprint.context = BlueprintSection(
        value=extract_result['extracted_fields'],
        status=FieldStatus.CONFIRMED
    )
    
    # Add more sections for complete blueprint
    session.blueprint.objective = BlueprintSection(
        value={"primary_goal": "Brand Awareness", "goal_note": "Aumentare visibilità brand"},
        status=FieldStatus.CONFIRMED
    )
    session.blueprint.target_market = BlueprintSection(
        value={"target_role": "Consumer finale", "geo_scope": "Italia"},
        status=FieldStatus.CONFIRMED
    )
    session.blueprint.value_prop = BlueprintSection(
        value={"offer_type": "E-commerce", "key_problem": "Moda sostenibile difficile da trovare"},
        status=FieldStatus.CONFIRMED
    )
    session.blueprint.channels_assets = BlueprintSection(
        value={"channels": ["Instagram", "TikTok", "Google Shopping"]},
        status=FieldStatus.CONFIRMED
    )
    session.blueprint.constraints = BlueprintSection(
        value={"budget_range": "3000-5000 euro/mese", "timing": "Q1 2026"},
        status=FieldStatus.CONFIRMED
    )
    
    # Step 3: Review
    print("\n📍 STEP 2: Review - Verify Blueprint")
    reviewer = ReviewService(real_llm)
    review_result = await reviewer.review_blueprint(session)
    
    print(f"  Confirmed items: {len(review_result['review']['confirmed'])}")
    print(f"  To confirm: {len(review_result['review']['to_confirm'])}")
    
    # Step 4: Generate
    print("\n📍 STEP 3: Generator - Create Output")
    generator = GenerationService(real_llm)
    generation_result = await generator.generate_output(session)
    
    print(f"  Slides created: {len(generation_result['slides'])}")
    print(f"  Report sections: {len(generation_result['report_sections'])}")
    print(f"  Assumptions: {len(generation_result.get('assumptions', []))}")
    
    # Final assertions
    assert len(generation_result['slides']) >= 6
    assert "review" in review_result
    
    print("\n✅ Complete workflow test passed!")
    print("="*80)


if __name__ == "__main__":
    print("""
    🧪 End-to-End LLM Integration Tests
    
    These tests make real API calls to OpenAI.
    
    Setup:
    1. Set OPENAI_API_KEY environment variable
    2. Run: pytest tests/test_e2e_llm.py -v -s
    
    Tests will be skipped if no API key is found.
    """)
