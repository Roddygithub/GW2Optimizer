"""
Test script pour l'API Team Commander en condition réelle.
"""

import requests
import json
from pprint import pprint

BASE_URL = "http://localhost:8000/api/v1"

def get_auth_token():
    """Get authentication token."""
    print("🔐 Authentification...")
    
    # Login
    response = requests.post(
        f"{BASE_URL}/auth/token",
        data={
            "username": "testcommander",
            "password": "TestPassword123!"
        }
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✅ Token obtenu: {token[:20]}...")
        return token
    else:
        print(f"❌ Erreur login: {response.status_code}")
        print(response.text)
        return None


def test_team_command(token, message):
    """Test team commander endpoint."""
    print(f"\n🎮 Test Team Commander")
    print(f"📝 Message: {message}")
    print("-" * 80)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {"message": message}
    
    response = requests.post(
        f"{BASE_URL}/ai/teams/command",
        headers=headers,
        json=payload
    )
    
    print(f"📊 Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("\n✅ RÉPONSE:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return result
    else:
        print(f"\n❌ ERREUR:")
        print(response.text)
        return None


def main():
    print("=" * 80)
    print("🚀 TEST API TEAM COMMANDER - CONDITION RÉELLE")
    print("=" * 80)
    
    # 1. Get token
    token = get_auth_token()
    if not token:
        print("\n❌ Impossible d'obtenir le token. Arrêt.")
        return
    
    print("\n" + "=" * 80)
    
    # 2. Test 1: Composition par classes
    print("\n📋 TEST 1: Composition par classes figées")
    test_team_command(
        token,
        "Je veux 2 groupes de 5 avec Firebrand, Druid, Harbinger, Spellbreaker, Scrapper"
    )
    
    print("\n" + "=" * 80)
    
    # 3. Test 2: Composition par rôles
    print("\n📋 TEST 2: Composition par rôles")
    test_team_command(
        token,
        "Je veux une équipe de 10 joueurs pour WvW. Dans chaque groupe il me faut un stabeur, un healer, un booner, un dps strip et un dps pur."
    )
    
    print("\n" + "=" * 80)
    print("✅ TESTS TERMINÉS")
    print("=" * 80)


if __name__ == "__main__":
    main()
