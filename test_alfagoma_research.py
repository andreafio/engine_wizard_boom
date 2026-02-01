"""
Test Research Service for Alfagoma SPA
"""
import asyncio
import json
from datetime import datetime
from app.services.research_service import research_company_intelligence


async def test_alfagoma_research():
    """
    Test research and intelligence gathering for Alfagoma SPA
    """
    print("=" * 80)
    print("RESEARCH & INTELLIGENCE - Alfagoma SPA")
    print("=" * 80)
    print()
    
    # Run research
    print("🔍 Avvio ricerca...")
    print()
    
    try:
        research = await research_company_intelligence(
            company_name="Alfagoma SPA",
            industry="Manifatturiero",  # Default, will be refined by AI
            website=None,  # Unknown
            session_id="alfagoma-research-test"
        )
        
        print("✅ Ricerca completata!")
        print()
        
        # Display results
        print("=" * 80)
        print("📊 RISULTATI RICERCA")
        print("=" * 80)
        print()
        
        print(f"🏢 Azienda: {research.company_name}")
        print(f"🏭 Settore: {research.industry}")
        if research.website_url:
            print(f"🌐 Website: {research.website_url}")
        print(f"📅 Data ricerca: {research.research_date}")
        print()
        
        # Social profiles
        print("-" * 80)
        print("📱 PRESENZA SOCIAL MEDIA")
        print("-" * 80)
        if research.social_profiles:
            for profile in research.social_profiles:
                print(f"\n{profile.platform.upper()}:")
                if profile.handle:
                    print(f"  Handle: @{profile.handle}")
                if profile.followers:
                    print(f"  Followers: {profile.followers:,}")
                if profile.posting_frequency:
                    print(f"  Frequenza post: {profile.posting_frequency}")
                if profile.content_themes:
                    print(f"  Temi: {', '.join(profile.content_themes)}")
                if profile.engagement_level:
                    print(f"  Engagement: {profile.engagement_level}")
        else:
            print("Nessun profilo social trovato")
        print()
        
        # Active campaigns
        print("-" * 80)
        print("📢 CAMPAGNE PUBBLICITARIE ATTIVE")
        print("-" * 80)
        if research.active_campaigns:
            for i, campaign in enumerate(research.active_campaigns, 1):
                print(f"\nCampagna {i} - {campaign.platform.upper()}:")
                print(f"  Titolo: {campaign.title}")
                print(f"  Descrizione: {campaign.description}")
                print(f"  Tipo media: {campaign.media_type}")
                print(f"  Attiva: {'Sì' if campaign.is_active else 'No'}")
                if campaign.started_running:
                    print(f"  Data inizio: {campaign.started_running}")
                if campaign.target_audience:
                    print(f"  Target: {campaign.target_audience}")
                if campaign.estimated_budget:
                    print(f"  Budget stimato: {campaign.estimated_budget}")
                if campaign.call_to_action:
                    print(f"  CTA: {campaign.call_to_action}")
                if campaign.landing_page:
                    print(f"  Landing: {campaign.landing_page}")
        else:
            print("Nessuna campagna pubblicitaria trovata")
        
        if research.ad_spend_estimate:
            print(f"\n💰 Spesa pubblicitaria stimata: {research.ad_spend_estimate}")
        print()
        
        # Competitors
        print("-" * 80)
        print("🏆 COMPETITOR IDENTIFICATI")
        print("-" * 80)
        if research.competitors:
            for i, competitor in enumerate(research.competitors, 1):
                print(f"\n{i}. {competitor.name}")
                if competitor.website:
                    print(f"   Website: {competitor.website}")
                if competitor.positioning:
                    print(f"   Posizionamento: {competitor.positioning}")
                if competitor.key_differentiators:
                    print(f"   Differenziatori:")
                    for diff in competitor.key_differentiators:
                        print(f"     • {diff}")
                if competitor.active_channels:
                    print(f"   Canali attivi: {', '.join(competitor.active_channels)}")
                if competitor.estimated_market_share:
                    print(f"   Market share: {competitor.estimated_market_share}")
        else:
            print("Nessun competitor identificato")
        print()
        
        # Marketing insights
        print("-" * 80)
        print("💡 MARKETING INSIGHTS")
        print("-" * 80)
        if research.marketing_insights:
            for i, insight in enumerate(research.marketing_insights, 1):
                print(f"{i}. {insight}")
        else:
            print("Nessun insight disponibile")
        print()
        
        # Recommended channels
        print("-" * 80)
        print("📊 CANALI RACCOMANDATI")
        print("-" * 80)
        if research.recommended_channels:
            for channel in research.recommended_channels:
                print(f"  ✓ {channel}")
        else:
            print("Nessuna raccomandazione disponibile")
        print()
        
        # Content gaps
        print("-" * 80)
        print("🎯 OPPORTUNITÀ CONTENUTI (Content Gaps)")
        print("-" * 80)
        if research.content_gaps:
            for gap in research.content_gaps:
                print(f"  → {gap}")
        else:
            print("Nessuna gap identificata")
        print()
        
        # Data sources
        print("-" * 80)
        print("📚 FONTI DATI")
        print("-" * 80)
        for source in research.data_sources:
            print(f"  • {source}")
        print()
        
        # Save to JSON
        output_file = "research_alfagoma_spa.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(research.model_dump(), f, indent=2, ensure_ascii=False)
        
        print("=" * 80)
        print(f"✅ Risultati salvati in: {output_file}")
        print("=" * 80)
        
        return research
        
    except Exception as e:
        print(f"❌ Errore durante la ricerca: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("\n🚀 Test Research Service - Alfagoma SPA\n")
    result = asyncio.run(test_alfagoma_research())
    
    if result:
        print("\n✅ Test completato con successo!")
    else:
        print("\n❌ Test fallito")
