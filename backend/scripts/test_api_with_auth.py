#!/usr/bin/env python
"""
Test API complet avec authentification.
"""

import requests
import json
import time
import random

API_BASE = "http://localhost:8000/api/v1"

def get_auth_token():
    """Crée un utilisateur de test et obtient un token."""
    # Utiliser un username unique pour éviter les conflits
    test_user = f"test_damage_{random.randint(1000, 9999)}"
    test_password = "TestPassword123!"
    
    print("1. Création d'un utilisateur de test...")
    try:
        response = requests.post(
            f"{API_BASE}/auth/register",
            json={
                "username": test_user,
                "email": f"{test_user}@test.com",
                "password": test_password
            }
        )
        
        if response.status_code == 200:
            print(f"   ✅ Utilisateur créé: {test_user}")
        elif response.status_code == 400 and "already registered" in response.text.lower():
            print(f"   ℹ️  Utilisateur existe déjà: {test_user}")
        else:
            print(f"   ⚠️  Statut: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️  Erreur d'inscription: {e}")
    
    # Se connecter pour obtenir le token
    print("\n2. Connexion et obtention du token...")
    try:
        response = requests.post(
            f"{API_BASE}/auth/login",
            data={
                "username": test_user,
                "password": test_password
            }
        )
        
        if response.status_code == 200:
            token_data = response.json()
            token = token_data.get("access_token")
            print(f"   ✅ Token obtenu: {token[:20]}...")
            return token
        else:
            print(f"   ❌ Échec de connexion: {response.status_code}")
            print(f"   {response.text}")
            return None
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return None


def test_build_analysis_with_auth():
    print("=" * 80)
    print("TEST EN CONDITION RÉELLE: API /ai/analyze/build avec Auth")
    print("=" * 80)
    print()
    
    # Obtenir un token d'authentification
    token = get_auth_token()
    if not token:
        print("\n❌ Impossible d'obtenir un token d'authentification")
        return
    
    # Build de test
    build_payload = {
        "specialization_id": 48,  # Tempest
        "trait_ids": [1952, 1839, 1902],
        "skill_ids": [
            5491,   # Fireball
            5528,   # Lava Font (Eruption)
            5501,   # Meteor Shower
            5638,   # Arcane Wave
        ],
        "context": "WvW Zerg - Test API Production"
    }
    
    print("\n3. Configuration du build:")
    print(f"   Specialization: {build_payload['specialization_id']} (Tempest)")
    print(f"   Skills: {len(build_payload['skill_ids'])} skills offensifs")
    
    print("\n4. Envoi de la requête authentifiée POST /ai/analyze/build...")
    print("   (Analyse IA: 10-30 secondes)")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{API_BASE}/ai/analyze/build",
            json=build_payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=300  # 5 minutes
        )
        
        elapsed = time.time() - start_time
        print(f"   ✅ Réponse reçue en {elapsed:.1f}s")
        
        if response.status_code != 200:
            print(f"   ❌ Erreur HTTP {response.status_code}")
            print(f"   {response.text}")
            return
        
        result = response.json()
        
        print("\n" + "=" * 80)
        print("5. RÉSULTATS DE L'ANALYSE")
        print("=" * 80)
        
        # Afficher le score et le résumé
        print(f"\n📊 Score de Synergie: {result.get('synergy_score', 'N/A')}")
        print(f"\n💬 Résumé de l'IA:")
        summary = result.get('summary', 'N/A')
        # Wrapper le texte à 70 caractères
        if len(summary) > 70:
            words = summary.split()
            lines = []
            current_line = []
            current_length = 0
            for word in words:
                if current_length + len(word) + 1 > 70:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                    current_length = len(word)
                else:
                    current_line.append(word)
                    current_length += len(word) + 1
            if current_line:
                lines.append(' '.join(current_line))
            for line in lines:
                print(f"   {line}")
        else:
            print(f"   {summary}")
        
        # Forces
        strengths = result.get('strengths', [])
        if strengths:
            print(f"\n✅ Forces ({len(strengths)}):")
            for i, strength in enumerate(strengths, 1):
                print(f"   {i}. {strength}")
        
        # Faiblesses
        weaknesses = result.get('weaknesses', [])
        if weaknesses:
            print(f"\n⚠️  Faiblesses ({len(weaknesses)}):")
            for i, weakness in enumerate(weaknesses, 1):
                print(f"   {i}. {weakness}")
        
        # Vérifier les dégâts estimés
        print("\n" + "=" * 80)
        print("6. VÉRIFICATION DES DÉGÂTS ESTIMÉS")
        print("=" * 80)
        
        build_data = result.get('build_data', {})
        skills = build_data.get('skills', [])
        
        print(f"\n🎯 Skills retournés: {len(skills)}")
        
        damage_skills = []
        
        for skill in skills:
            skill_id = skill.get('id')
            skill_name = skill.get('name')
            estimated_damage = skill.get('estimated_damage_berserker')
            
            print(f"\n   Skill: {skill_name} (ID: {skill_id})")
            
            if estimated_damage is not None:
                print(f"   ✅ estimated_damage_berserker: {estimated_damage:.2f}")
                damage_skills.append((skill_name, estimated_damage))
                
                # Vérifier si l'IA mentionne ce skill
                full_text = json.dumps(result, ensure_ascii=False).lower()
                if skill_name.lower() in full_text:
                    print(f"   🤖 Mentionné par l'IA dans l'analyse")
            else:
                print(f"   ℹ️  Pas de dégâts estimés (skill non-offensif)")
        
        # Comparaison des dégâts
        if len(damage_skills) > 1:
            print(f"\n📊 Comparaison des dégâts (Profil Berserker Power=2500):")
            damage_skills.sort(key=lambda x: x[1], reverse=True)
            max_dmg = max(d[1] for d in damage_skills)
            for i, (name, dmg) in enumerate(damage_skills, 1):
                bar_len = int((dmg / max_dmg) * 30)
                bar = "█" * bar_len
                print(f"   {i}. {name:20s} {dmg:7.1f}  {bar}")
        
        # Validation
        print("\n" + "=" * 80)
        print("7. VALIDATION DU SYSTÈME")
        print("=" * 80)
        
        checks = []
        
        # Check estimated_damage
        if damage_skills:
            checks.append(("✅", f"{len(damage_skills)} skills avec estimated_damage_berserker"))
        else:
            checks.append(("❌", "Aucun estimated_damage_berserker trouvé"))
        
        # Check mention IA
        full_text = json.dumps(result, ensure_ascii=False).lower()
        ai_mentions_damage = any(kw in full_text for kw in ['damage', 'dégât', 'burst', 'dps'])
        if ai_mentions_damage:
            checks.append(("✅", "L'IA discute des dégâts"))
        
        # Check performance
        checks.append(("✅", f"Requête complétée en {elapsed:.1f}s"))
        
        # Check authentification
        checks.append(("✅", "Authentification JWT fonctionnelle"))
        
        print()
        for status, message in checks:
            print(f"   {status} {message}")
        
        print("\n" + "=" * 80)
        if all(c[0] == "✅" for c in checks):
            print("🎉 TEST RÉUSSI - Système opérationnel en production!")
        else:
            print("⚠️  Test partiel")
        print("=" * 80)
        
        # Sauvegarder
        with open('/tmp/api_auth_test_response.json', 'w') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print("\n💾 Réponse complète: /tmp/api_auth_test_response.json")
        
    except requests.Timeout:
        print(f"   ❌ Timeout après {time.time() - start_time:.1f}s")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_build_analysis_with_auth()
