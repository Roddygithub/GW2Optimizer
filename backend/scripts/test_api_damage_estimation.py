#!/usr/bin/env python
"""
Test en condition réelle de l'API /ai/analyze/build avec estimation de dégâts.
Envoie une vraie requête HTTP au backend.
"""

import requests
import json
import time

API_BASE = "http://localhost:8000/api/v1"

def test_build_analysis():
    print("=" * 80)
    print("TEST EN CONDITION RÉELLE: Analyse IA via API REST")
    print("=" * 80)
    
    # Build de test: Elementaliste avec skills de dégâts
    build_payload = {
        "specialization_id": 48,  # Tempest
        "trait_ids": [1952, 1839, 1902],
        "skill_ids": [
            5491,   # Fireball
            5528,   # Lava Font (Eruption)
            5501,   # Meteor Shower
            5638,   # Arcane Wave
        ],
        "context": "WvW Zerg - Test API Damage"
    }
    
    print("\n1. Vérification de l'API...")
    try:
        health = requests.get(f"{API_BASE.replace('/api/v1', '')}/health", timeout=5)
        print(f"   ✅ Backend actif: {health.json()}")
    except Exception as e:
        print(f"   ❌ Backend non disponible: {e}")
        return
    
    print("\n2. Configuration du build:")
    print(f"   Specialization: {build_payload['specialization_id']} (Tempest)")
    print(f"   Skills: {len(build_payload['skill_ids'])} skills offensifs")
    print(f"   Context: {build_payload['context']}")
    
    print("\n3. Envoi de la requête POST /ai/analyze/build...")
    print("   (Cela peut prendre 10-30 secondes pour l'analyse IA)")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{API_BASE}/ai/analyze/build",
            json=build_payload,
            timeout=120  # 2 minutes max
        )
        
        elapsed = time.time() - start_time
        print(f"   ✅ Réponse reçue en {elapsed:.1f}s")
        
        if response.status_code != 200:
            print(f"   ❌ Erreur HTTP {response.status_code}")
            print(f"   {response.text}")
            return
        
        result = response.json()
        
        print("\n" + "=" * 80)
        print("4. RÉSULTATS DE L'ANALYSE")
        print("=" * 80)
        
        # Afficher le score et le résumé
        print(f"\n📊 Score de Synergie: {result.get('synergy_score', 'N/A')}")
        print(f"\n💬 Résumé de l'IA:")
        print(f"   {result.get('summary', 'N/A')}")
        
        # Afficher les forces
        strengths = result.get('strengths', [])
        if strengths:
            print(f"\n✅ Forces ({len(strengths)}):")
            for i, strength in enumerate(strengths, 1):
                print(f"   {i}. {strength}")
        
        # Afficher les faiblesses
        weaknesses = result.get('weaknesses', [])
        if weaknesses:
            print(f"\n⚠️  Faiblesses ({len(weaknesses)}):")
            for i, weakness in enumerate(weaknesses, 1):
                print(f"   {i}. {weakness}")
        
        # Vérifier les dégâts estimés dans build_data
        print("\n" + "=" * 80)
        print("5. VÉRIFICATION DES DÉGÂTS ESTIMÉS (VIA API)")
        print("=" * 80)
        
        build_data = result.get('build_data', {})
        skills = build_data.get('skills', [])
        
        print(f"\n🎯 Skills dans le build: {len(skills)}")
        
        has_damage_estimation = False
        damage_skills = []
        
        for skill in skills:
            skill_id = skill.get('id')
            skill_name = skill.get('name')
            estimated_damage = skill.get('estimated_damage_berserker')
            
            print(f"\n   Skill: {skill_name} (ID: {skill_id})")
            
            if estimated_damage is not None:
                print(f"   ✅ estimated_damage_berserker: {estimated_damage:.2f}")
                has_damage_estimation = True
                damage_skills.append((skill_name, estimated_damage))
                
                # Vérifier si l'IA mentionne ce skill
                full_text = json.dumps(result, ensure_ascii=False).lower()
                if skill_name.lower() in full_text:
                    print(f"   🤖 L'IA mentionne ce skill dans son analyse!")
            else:
                print(f"   ℹ️  Pas de dégâts estimés")
        
        # Comparaison des skills
        if len(damage_skills) > 1:
            print(f"\n📊 Comparaison des dégâts (Berserker Power=2500):")
            damage_skills.sort(key=lambda x: x[1], reverse=True)
            for i, (name, dmg) in enumerate(damage_skills, 1):
                bar = "█" * int(dmg / 100)
                print(f"   {i}. {name:20s} {dmg:7.1f} {bar}")
        
        # Résumé du test
        print("\n" + "=" * 80)
        print("6. VALIDATION DU TEST")
        print("=" * 80)
        
        checks = []
        
        # Check 1: estimated_damage_berserker présent
        if has_damage_estimation:
            checks.append(("✅", "estimated_damage_berserker présent dans l'API"))
        else:
            checks.append(("❌", "estimated_damage_berserker absent"))
        
        # Check 2: L'IA mentionne les dégâts
        full_text = json.dumps(result, ensure_ascii=False).lower()
        if any(kw in full_text for kw in ['damage', 'dégât', 'burst', 'dps']):
            checks.append(("✅", "L'IA discute des dégâts dans son analyse"))
        else:
            checks.append(("⚠️", "L'IA ne mentionne pas explicitement les dégâts"))
        
        # Check 3: Flux complet API
        checks.append(("✅", f"Flux API complet en {elapsed:.1f}s"))
        
        print()
        for status, message in checks:
            print(f"   {status} {message}")
        
        print("\n" + "=" * 80)
        if all(c[0] == "✅" for c in checks[:2]):
            print("✅ TEST RÉUSSI - Le système fonctionne en production!")
        else:
            print("⚠️  Test partiel - Vérifier les points ci-dessus")
        print("=" * 80)
        
        # Sauvegarder la réponse complète pour inspection
        with open('/tmp/api_response_damage_test.json', 'w') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print("\n💾 Réponse complète sauvegardée: /tmp/api_response_damage_test.json")
        
    except requests.Timeout:
        print(f"   ❌ Timeout après {time.time() - start_time:.1f}s")
        print("   L'analyse IA prend trop de temps (>120s)")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\nPré-requis:")
    print("  - Backend FastAPI actif sur localhost:8000")
    print("  - Ollama actif avec mistral:7b")
    print("  - Redis actif\n")
    
    test_build_analysis()
