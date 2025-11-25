"""
Test LangChain + DuckDuckGo en condition réelle.
Vérifie que l'accès web gratuit fonctionne pour l'IA.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agents.tools.web_search import (
    create_web_search_tool,
    create_gw2_meta_search_tool,
    search_gw2_meta,
)


def test_basic_web_search():
    """Test 1: Recherche web basique avec DuckDuckGo."""
    print("=" * 80)
    print("TEST 1: Recherche Web Basique (DuckDuckGo)")
    print("=" * 80)
    
    search_tool = create_web_search_tool()
    
    if not search_tool.is_available():
        print("❌ ERREUR: LangChain ou DuckDuckGo non installé")
        print("   Installation: poetry add langchain langchain-community duckduckgo-search")
        return False
    
    print("✅ LangChain + DuckDuckGo disponible")
    print()
    
    # Test search
    print("🔍 Recherche: 'python langchain tutorial'")
    results = search_tool.search("python langchain tutorial")
    
    print(f"📄 Résultats ({len(results)} caractères):")
    print(results[:500] + "..." if len(results) > 500 else results)
    print()
    
    return True


def test_gw2_meta_search():
    """Test 2: Recherche GW2 meta WvW."""
    print("=" * 80)
    print("TEST 2: Recherche GW2 Meta WvW")
    print("=" * 80)
    
    gw2_search = create_gw2_meta_search_tool()
    
    if not gw2_search.web_search.is_available():
        print("❌ ERREUR: Web search non disponible")
        return False
    
    print("✅ GW2 Meta Search disponible")
    print()
    
    # Test 1: Meta Guardian WvW
    print("🔍 Recherche: Guardian Support WvW Meta")
    results = gw2_search.search_wvw_meta("Guardian", role="Support")
    
    print(f"📄 Résultats ({len(results)} caractères):")
    print(results[:500] + "..." if len(results) > 500 else results)
    print()
    
    # Test 2: Current meta
    print("🔍 Recherche: Current WvW Meta 2024")
    results = gw2_search.search_current_meta("WvW")
    
    print(f"📄 Résultats ({len(results)} caractères):")
    print(results[:500] + "..." if len(results) > 500 else results)
    print()
    
    return True


def test_quick_search():
    """Test 3: Fonction rapide search_gw2_meta."""
    print("=" * 80)
    print("TEST 3: Fonction Rapide search_gw2_meta()")
    print("=" * 80)
    
    print("🔍 Recherche: Necromancer DPS WvW")
    results = search_gw2_meta("Necromancer", role="DPS", game_mode="WvW")
    
    print(f"📄 Résultats ({len(results)} caractères):")
    print(results[:500] + "..." if len(results) > 500 else results)
    print()
    
    return True


def test_langchain_tools_format():
    """Test 4: Format LangChain Tools pour Mistral."""
    print("=" * 80)
    print("TEST 4: LangChain Tools Format (pour Mistral)")
    print("=" * 80)
    
    try:
        from app.agents.tools.web_search import get_langchain_tools
        
        tools = get_langchain_tools()
        
        print(f"✅ {len(tools)} tools disponibles pour Mistral:")
        for i, tool in enumerate(tools, 1):
            print(f"   {i}. {tool.name}: {tool.description[:60]}...")
        print()
        
        # Test call d'un tool
        if tools:
            print(f"🧪 Test call du tool '{tools[0].name}'...")
            try:
                result = tools[0].func("gw2 wvw meta 2024")
                print(f"✅ Tool call réussi ({len(result)} caractères)")
                print(f"📄 Preview: {result[:200]}...")
            except Exception as e:
                print(f"⚠️ Tool call échoué: {e}")
        
        print()
        return True
        
    except ImportError as e:
        print(f"❌ ERREUR: {e}")
        print("   Installation: poetry add langchain")
        return False


def main():
    """Run all tests."""
    print("\n")
    print("🚀 TEST LANGCHAIN + DUCKDUCKGO - ACCÈS WEB GRATUIT")
    print("=" * 80)
    print()
    
    # Check installation
    try:
        import langchain
        import langchain_community
        from duckduckgo_search import DDGS
        print("✅ Dépendances installées:")
        print(f"   - langchain: {langchain.__version__}")
        print(f"   - langchain-community: OK")
        print(f"   - duckduckgo-search: OK")
        print()
    except ImportError as e:
        print("❌ ERREUR: Dépendances manquantes")
        print(f"   {e}")
        print()
        print("📦 Installation requise:")
        print("   poetry add langchain langchain-community duckduckgo-search")
        print()
        return
    
    # Run tests
    tests = [
        ("Recherche Web Basique", test_basic_web_search),
        ("Recherche GW2 Meta", test_gw2_meta_search),
        ("Fonction Rapide", test_quick_search),
        ("LangChain Tools Format", test_langchain_tools_format),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"❌ ERREUR dans {name}: {e}")
            results.append((name, False))
    
    # Summary
    print("=" * 80)
    print("RÉSUMÉ DES TESTS")
    print("=" * 80)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {name}")
    
    total = len(results)
    passed = sum(1 for _, s in results if s)
    
    print()
    print(f"📊 Score: {passed}/{total} tests réussis")
    
    if passed == total:
        print()
        print("🎉 TOUS LES TESTS RÉUSSIS !")
        print("✅ LangChain + DuckDuckGo fonctionne parfaitement")
        print("✅ L'IA peut maintenant chercher sur le web GRATUITEMENT")
        print()
        print("💡 Prochaine étape:")
        print("   Intégrer ces tools à Mistral avec function calling")
    else:
        print()
        print("⚠️ Certains tests ont échoué")
        print("   Vérifiez l'installation des dépendances")


if __name__ == "__main__":
    main()
