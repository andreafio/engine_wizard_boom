#!/usr/bin/env python3
"""
Demo script for Quality Critic Service
Shows the service working with the exact specification format
"""
import asyncio
import os
from app.services.quality_critic_service import critique_wizard_answer


async def demo_quality_critic():
    """Demonstrate quality critic with various answer types"""

    print("🎯 Quality Critic Service Demo")
    print("=" * 50)

    # Test cases matching the specification format
    test_cases = [
        {
            "field": "context.industry",
            "value": "Tech",
            "ui_type": "short_text",
            "section": "Context",
            "description": "Vague industry answer"
        },
        {
            "field": "context.industry",
            "value": "Software development and cloud computing services",
            "ui_type": "short_text",
            "section": "Context",
            "description": "Specific industry answer"
        },
        {
            "field": "objective.goal",
            "value": "Grow business",
            "ui_type": "long_text",
            "section": "Objective",
            "description": "Vague goal answer"
        },
        {
            "field": "objective.goal",
            "value": "Increase monthly recurring revenue by 25% within 6 months through targeted digital marketing campaigns and improved customer retention strategies",
            "ui_type": "long_text",
            "section": "Objective",
            "description": "Specific goal answer"
        },
        {
            "field": "audience.target_audience",
            "value": ["Small businesses", "Startups"],
            "ui_type": "multi_select",
            "section": "Audience",
            "description": "Multi-select audience answer"
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test Case {i}: {test_case['description']}")
        print(f"Input: {test_case}")

        try:
            result = await critique_wizard_answer(
                field=test_case["field"],
                value=test_case["value"],
                ui_type=test_case["ui_type"],
                section=test_case["section"]
            )

            print("✅ Output:")
            print(f"   Quality Score: {result.quality_score}")
            print(f"   Recommend Follow-up: {result.recommend_deep_followup}")
            print(f"   Follow-up Field: {result.followup_field}")
            print(f"   Reason: {result.reason}")

        except Exception as e:
            print(f"❌ Error: {e}")

    print("\n" + "=" * 50)
    print("🎉 Demo completed!")


if __name__ == "__main__":
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Please set OPENAI_API_KEY environment variable")
        exit(1)

    asyncio.run(demo_quality_critic())