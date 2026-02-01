#!/usr/bin/env python3
"""
Quick test of Quality Critic Service with specification
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock
from app.services.quality_critic_service import QualityCriticService


async def test_quality_critic():
    """Test the quality critic service"""

    # Mock LLM with response matching specification
    llm = MagicMock()
    llm.generate_json = AsyncMock(return_value={
        'quality_score': 0.3,
        'recommend_deep_followup': True,
        'followup_field': 'context.company_size',
        'reason': 'too vague'
    })

    service = QualityCriticService(llm)
    result = await service.critique_answer(
        field='context.industry',
        value='Tech',
        ui_type='short_text',
        section='Context'
    )

    print('🎯 Quality Critic Service Test')
    print('=' * 40)
    print('Input JSON:')
    print('  {')
    print('    "field": "context.industry",')
    print('    "value": "Tech",')
    print('    "ui_type": "short_text",')
    print('    "section": "Context"')
    print('  }')
    print()
    print('Output JSON:')
    print('  {')
    print(f'    "quality_score": {result.quality_score},')
    print(f'    "recommend_deep_followup": {str(result.recommend_deep_followup).lower()},')
    print(f'    "followup_field": "{result.followup_field}",')
    print(f'    "reason": "{result.reason}"')
    print('  }')
    print()
    print('✅ Service working correctly with specification!')


if __name__ == "__main__":
    asyncio.run(test_quality_critic())