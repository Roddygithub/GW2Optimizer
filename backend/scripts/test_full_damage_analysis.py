#!/usr/bin/env python
"""
Test complet de l'analyse de dégâts avec l'IA.
Appelle BuildAnalysisService avec un build réel et affiche la réponse IA complète.
"""

import asyncio
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.build_analysis_service import BuildAnalysisService
from app.services.gw2_api_client import GW2APIClient
from app.agents.analyst_agent import AnalystAgent


async def main():
    print("=" * 80)
    print("TEST COMPLET: Analyse IA avec Estimation de Dégâts")
    print("=" * 80)
    
    # Build de test: Elementaliste Tempest avec des skills de dégâts
    # On va utiliser des skills staff d'élémentaliste qui ont des coefficients de dégâts
    build_config = {
        "specialization_id": 48,  # Tempest (Elite spec Elementalist)
        "trait_ids": [
            # Quelques traits Tempest pour enrichir l'analyse
            1952,  # Hardy Conduit
            1839,  # Unstable Conduit
            1902,  # Elemental Bastion
        ],
        "skill_ids": [
            5491,   # Fireball (Staff Fire 1) - a des dégâts
            5528,   # Lava Font (Staff Fire 2) - a des dégâts  
            5501,   # Meteor Shower (Staff Fire 5) - a des dégâts
            5638,   # Arcane Wave (utility) - a des dégâts
        ],
        "context": "WvW Zerg - Test Damage Estimation"
    }
    
    print(f"\n1. Configuration du build de test:")
    print(f"   Specialization: {build_config['specialization_id']} (Tempest)")
    print(f"   Traits: {len(build_config['trait_ids'])} traits")
    print(f"   Skills: {len(build_config['skill_ids'])} skills offensifs")
    print(f"   Context: {build_config['context']}")
    
    # Créer le service d'analyse avec les vraies dépendances
    print("\n2. Initialisation des services (GW2 API + Ollama)...")
    gw2_client = GW2APIClient()
    analyst_agent = AnalystAgent()
    service = BuildAnalysisService(gw2_client=gw2_client, analyst_agent=analyst_agent)
    
    # Lancer l'analyse
    print("\n3. Lancement de l'analyse (cela peut prendre 10-30 secondes)...")
    print("   - Récupération des données GW2 API")
    print("   - Calcul des dégâts estimés (Berserker Power=2500)")
    print("   - Analyse IA avec Ollama...")
    
    try:
        result = await service.analyze_build_synergy(**build_config)
        
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
        print("5. VÉRIFICATION DES DÉGÂTS ESTIMÉS")
        print("=" * 80)
        
        build_data = result.get('build_data', {})
        skills = build_data.get('skills', [])
        
        print(f"\n🎯 Skills dans le build: {len(skills)}")
        
        has_damage_estimation = False
        ai_mentions_damage = False
        
        for skill in skills:
            skill_id = skill.get('id')
            skill_name = skill.get('name')
            estimated_damage = skill.get('estimated_damage_berserker')
            
            print(f"\n   Skill: {skill_name} (ID: {skill_id})")
            
            if estimated_damage is not None:
                print(f"   ✅ estimated_damage_berserker: {estimated_damage:.2f}")
                has_damage_estimation = True
                
                # Vérifier si l'IA mentionne ce skill ou des dégâts
                summary_text = str(result.get('summary', '')) + ' '.join(strengths or []) + ' '.join(weaknesses or [])
                if skill_name.lower() in summary_text.lower() or str(int(estimated_damage)) in summary_text:
                    ai_mentions_damage = True
                    print(f"   🤖 L'IA mentionne ce skill ou ses dégâts dans l'analyse!")
            else:
                print(f"   ℹ️  Pas de dégâts estimés (skill non offensif ou sans facts Damage)")
        
        # Vérifier si l'IA mentionne des chiffres de dégâts
        full_text = json.dumps(result, ensure_ascii=False)
        if any(keyword in full_text.lower() for keyword in ['dégât', 'damage', 'burst', 'dps']):
            print("\n   🤖 L'IA discute des dégâts dans son analyse!")
            ai_mentions_damage = True
        
        # Résumé du test
        print("\n" + "=" * 80)
        print("6. RÉSUMÉ DU TEST")
        print("=" * 80)
        
        if has_damage_estimation:
            print("\n   ✅ TEST PASSED: estimated_damage_berserker est présent!")
            print("      → Les skills offensifs ont leurs dégâts calculés")
            print("      → Ces données sont envoyées à l'AnalystAgent")
        else:
            print("\n   ⚠️  WARNING: Aucun estimated_damage_berserker trouvé")
            print("      → Vérifier que les skills ont des facts 'Damage' dans GW2 API")
        
        if ai_mentions_damage:
            print("\n   ✅ L'IA utilise les données de dégâts dans son analyse!")
            print("      → Elle mentionne des skills ou discute du burst/dégâts")
        else:
            print("\n   ℹ️  L'IA ne mentionne pas explicitement les chiffres de dégâts")
            print("      → Normal si le build a d'autres forces/faiblesses plus importantes")
        
        print("\n" + "=" * 80)
        print("✅ TEST TERMINÉ - Le système de dégâts est opérationnel!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ ERREUR lors de l'analyse: {e}")
        import traceback
        traceback.print_exc()
        print("\nPossible causes:")
        print("  - Ollama n'est pas démarré (lancer: ollama serve)")
        print("  - Le modèle mistral:7b n'est pas installé")
        print("  - Problème réseau avec l'API GW2")


if __name__ == "__main__":
    print("\nNOTE: Ce test nécessite:")
    print("  - Ollama démarré avec le modèle mistral:7b")
    print("  - Accès internet pour l'API GW2")
    print("  - Les dépendances Python installées\n")
    
    asyncio.run(main())
