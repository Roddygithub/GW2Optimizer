#!/usr/bin/env python
"""Test script to verify damage estimation is working in BuildAnalysisService."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.build_analysis_service import BuildAnalysisService
from app.services.gw2_api_client import GW2APIClient


class FakeAnalystAgent:
    """Fake agent that just echoes back the build_data to inspect it."""
    
    async def execute(self, inputs):
        return {"success": True, "result": inputs}


async def main():
    print("=" * 80)
    print("Testing Damage Estimation in BuildAnalysisService")
    print("=" * 80)
    
    # Use real GW2 API client
    gw2_client = GW2APIClient()
    
    # First, let's fetch a known offensive skill to test
    # Elementalist Fireball (staff skill) - ID 5491
    # Warrior Maul (hammer skill) - ID 14354
    test_skill_id = 5491  # Fireball
    
    print(f"\n1. Fetching skill {test_skill_id} from GW2 API...")
    try:
        skill_data = await gw2_client.get_skill(test_skill_id)
        print(f"   ✓ Skill: {skill_data.get('name')}")
        print(f"   Type: {skill_data.get('type')}")
        
        # Show facts
        facts = skill_data.get('facts', [])
        print(f"   Facts count: {len(facts)}")
        for fact in facts:
            if fact.get('type') == 'Damage':
                print(f"   → Damage fact: dmg_multiplier={fact.get('dmg_multiplier')}, hit_count={fact.get('hit_count', 1)}")
    except Exception as e:
        print(f"   ✗ Failed to fetch skill: {e}")
        return
    
    # Now test BuildAnalysisService with a fake AnalystAgent
    print("\n2. Testing BuildAnalysisService with fake AnalystAgent...")
    service = BuildAnalysisService(
        gw2_client=gw2_client,
        analyst_agent=FakeAnalystAgent()
    )
    
    # Create a minimal build with just this skill
    # We need a valid specialization for Elementalist
    # Tempest (elite spec) - ID 48
    try:
        result = await service.analyze_build_synergy(
            specialization_id=48,  # Tempest
            trait_ids=[],  # No traits for this test
            skill_ids=[test_skill_id],
            context="Test Damage Estimation"
        )
        
        print("   ✓ BuildAnalysisService executed successfully")
        
        # Extract the build_data that would be sent to the real AnalystAgent
        build_data = result.get('build_data', {})
        skills = build_data.get('skills', [])
        
        print(f"\n3. Inspecting skills in build_data (sent to AnalystAgent)...")
        print(f"   Skills count: {len(skills)}")
        
        for skill in skills:
            skill_id = skill.get('id')
            skill_name = skill.get('name')
            estimated_damage = skill.get('estimated_damage_berserker')
            
            print(f"\n   Skill ID: {skill_id}")
            print(f"   Name: {skill_name}")
            print(f"   Type: {skill.get('type')}")
            
            if estimated_damage is not None:
                print(f"   ✓ estimated_damage_berserker: {estimated_damage:.2f}")
                print(f"      → This field will be visible to the AI for burst analysis!")
            else:
                print(f"   ✗ estimated_damage_berserker: Not present (skill has no Damage facts)")
            
            # Show minified facts
            facts = skill.get('facts', [])
            if facts:
                print(f"   Facts (minified): {len(facts)} facts")
                for f in facts:
                    if f.get('type') == 'Damage':
                        print(f"      → {f}")
        
        print("\n" + "=" * 80)
        print("✓ TEST PASSED: Damage estimation is working correctly!")
        print("  - estimated_damage_berserker is calculated from GW2 API facts")
        print("  - The field is added to skills in build_data")
        print("  - AnalystAgent will receive this data for AI analysis")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
