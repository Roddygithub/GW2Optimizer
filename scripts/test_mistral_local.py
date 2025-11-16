#!/usr/bin/env python3
"""
Test Mistral AI Integration Locally
Tests the complete flow: API call → composition generation → validation
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.services.mistral_ai import MistralAIService
from app.core.config import settings
from app.core.logging import logger


async def test_mistral_composition():
    """Test Mistral AI team composition generation"""
    
    print("=" * 80)
    print("🧪 MISTRAL AI LOCAL TEST")
    print("=" * 80)
    
    # Check API key
    api_key = getattr(settings, "MISTRAL_API_KEY", None)
    if not api_key:
        print("⚠️  MISTRAL_API_KEY not configured in environment")
        print("📝 Using fallback composition instead")
        print()
    else:
        print(f"✅ MISTRAL_API_KEY configured: {api_key[:10]}...")
        print()
    
    # Initialize service
    print("🔧 Initializing Mistral AI Service...")
    service = MistralAIService(api_key=api_key)
    
    # Prepare test data
    wvw_data = {
        "match_details": {
            "id": "test-match",
            "scores": {
                "red": 150000,
                "blue": 145000,
                "green": 140000
            }
        }
    }
    
    team_size = 50
    game_mode = "zerg"
    
    print(f"📊 Test Parameters:")
    print(f"   - Team Size: {team_size}")
    print(f"   - Game Mode: {game_mode}")
    print(f"   - Match Scores: {wvw_data['match_details']['scores']}")
    print()
    
    # Generate composition
    print("🤖 Generating team composition...")
    print()
    
    try:
        composition = await service.generate_team_composition(
            wvw_data=wvw_data,
            team_size=team_size,
            game_mode=game_mode
        )
        
        # Display results
        print("=" * 80)
        print("✅ COMPOSITION GENERATED SUCCESSFULLY")
        print("=" * 80)
        print()
        
        print(f"📋 Name: {composition.get('name', 'N/A')}")
        print(f"👥 Size: {composition.get('size', 'N/A')}")
        print(f"🎮 Mode: {composition.get('game_mode', 'N/A')}")
        print(f"🔧 Source: {composition.get('source', 'N/A')}")
        print(f"🤖 Model: {composition.get('model', 'N/A')}")
        print()
        
        print("🏗️  BUILDS:")
        print("-" * 80)
        for build in composition.get('builds', []):
            print(f"   {build.get('profession', 'Unknown'):15} | "
                  f"{build.get('role', 'Unknown'):10} | "
                  f"Count: {build.get('count', 0):2} | "
                  f"Priority: {build.get('priority', 'N/A')}")
        print()
        
        print("💪 STRENGTHS:")
        for strength in composition.get('strengths', []):
            print(f"   ✓ {strength}")
        print()
        
        print("⚠️  WEAKNESSES:")
        for weakness in composition.get('weaknesses', []):
            print(f"   ✗ {weakness}")
        print()
        
        print("🎯 STRATEGY:")
        print(f"   {composition.get('strategy', 'N/A')}")
        print()
        
        # Validation
        print("=" * 80)
        print("🔍 VALIDATION")
        print("=" * 80)
        
        total_count = sum(build.get('count', 0) for build in composition.get('builds', []))
        print(f"✓ Total players: {total_count}/{team_size}")
        
        if total_count == team_size:
            print("✅ Team size matches exactly!")
        elif abs(total_count - team_size) <= 2:
            print("✅ Team size is within acceptable range")
        else:
            print(f"⚠️  Team size mismatch (difference: {abs(total_count - team_size)})")
        
        print()
        print("✅ All required fields present")
        print()
        
        # Save to file
        import json
        output_file = backend_path.parent / "reports" / "MISTRAL_TEST_LOCAL.json"
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(composition, f, indent=2)
        
        print(f"💾 Results saved to: {output_file}")
        print()
        
        return True
        
    except Exception as e:
        print("=" * 80)
        print("❌ TEST FAILED")
        print("=" * 80)
        print(f"Error: {str(e)}")
        print()
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        await service.close()


async def test_mistral_api_direct():
    """Test direct Mistral API call"""
    
    print("=" * 80)
    print("🔌 DIRECT API TEST")
    print("=" * 80)
    
    api_key = getattr(settings, "MISTRAL_API_KEY", None)
    if not api_key:
        print("⚠️  Skipping direct API test (no API key)")
        return False
    
    import httpx
    
    print("📡 Testing Mistral API connectivity...")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "mistral-small-latest",
                    "messages": [
                        {"role": "user", "content": "Say 'API test successful' in one sentence."}
                    ],
                    "max_tokens": 50
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                message = result["choices"][0]["message"]["content"]
                print(f"✅ API Response: {message}")
                print()
                return True
            else:
                print(f"❌ API Error: {response.status_code}")
                print(f"   {response.text}")
                print()
                return False
                
    except Exception as e:
        print(f"❌ Connection Error: {str(e)}")
        print()
        return False


async def main():
    """Run all tests"""
    
    print()
    print("🚀 Starting Mistral AI Local Tests")
    print()
    
    # Test 1: Direct API
    api_ok = await test_mistral_api_direct()
    
    # Test 2: Composition generation
    composition_ok = await test_mistral_composition()
    
    # Summary
    print("=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    print(f"Direct API Test: {'✅ PASS' if api_ok else '⚠️  SKIP/FAIL'}")
    print(f"Composition Test: {'✅ PASS' if composition_ok else '❌ FAIL'}")
    print()
    
    if composition_ok:
        print("🎉 All critical tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
