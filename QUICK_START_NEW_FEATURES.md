# 🚀 QUICK START - Nouvelles Fonctionnalités

## Installation Immédiate (Gratuit, Pas d'API Key)

```bash
cd /home/roddy/GW2Optimizer/backend

# Installer LangChain + DuckDuckGo (100% gratuit)
poetry add langchain langchain-community langchain-ollama duckduckgo-search
```

---

## 1. Tester la Recherche Web (DuckDuckGo Gratuit)

### Recherche Basique
```bash
poetry run python -c "
from app.agents.tools import create_web_search_tool

search = create_web_search_tool()
results = search.search('best necro build gw2 wvw 2024')
print(results)
"
```

### Recherche GW2 Spécialisée
```bash
poetry run python -c "
from app.agents.tools import search_gw2_meta

# Chercher meta WvW pour Guardian Support
results = search_gw2_meta('Guardian', role='Support', game_mode='WvW')
print(results)
"
```

---

## 2. Tester le Traits Parser

### Parser un Trait Simple
```bash
poetry run python -c "
from app.engine.parsers import TraitParser

parser = TraitParser(game_mode='WvW')

# Exemple de trait
trait_data = {
    'name': 'Fiery Wrath',
    'description': 'Deal 10% more damage to burning foes.',
    'facts': [
        {'type': 'AttributeAdjust', 'target': 'Power', 'value': 180}
    ]
}

modifiers = parser.parse_trait(trait_data)
for mod in modifiers:
    print(f'{mod.name}: {mod.value} ({mod.modifier_type})')
"
```

### Parser Plusieurs Traits
```bash
poetry run python -c "
from app.engine.parsers import parse_traits_for_build

traits_data = [
    {'name': 'Fiery Wrath', 'description': 'Deal 10% more damage', 'facts': []},
    {'name': 'Radiant Power', 'description': '+180 Power', 'facts': [
        {'type': 'AttributeAdjust', 'target': 'Power', 'value': 180}
    ]},
]

modifiers = parse_traits_for_build(traits_data, game_mode='WvW')
print(f'Found {len(modifiers)} modifiers')
for mod in modifiers:
    print(f'  - {mod.name}: {mod.value}')
"
```

---

## 3. Tester les Nouvelles Runes/Sigils

### Lister Toutes les Runes Disponibles
```bash
poetry run python -c "
from app.engine.gear.registry import RUNE_REGISTRY

print('=== RUNES WvW META ===')
for rune_name in RUNE_REGISTRY.keys():
    print(f'  - {rune_name}')
"
```

### Lister Tous les Sigils Disponibles
```bash
poetry run python -c "
from app.engine.gear.registry import SIGIL_REGISTRY

print('=== SIGILS WvW META ===')
for sigil_name in SIGIL_REGISTRY.keys():
    print(f'  - {sigil_name}')
"
```

### Tester une Nouvelle Rune (Monk)
```bash
poetry run python -c "
from app.engine.gear.registry import RUNE_REGISTRY

monk_runes = RUNE_REGISTRY['Monk']()
print('=== RUNE OF THE MONK ===')
for rune in monk_runes:
    print(f'{rune.name}: +{rune.value} {rune.target_stat or rune.modifier_type}')
"
```

---

## 4. Tester l'Optimizer avec les Nouvelles Options

### Test Optimizer Support (5 runes au lieu de 1)
```bash
poetry run python -c "
from app.agents.build_equipment_optimizer import get_build_optimizer

optimizer = get_build_optimizer()

# Les runes testées pour Support
runes = optimizer._get_wvw_meta_runes('support')
print(f'Support testera {len(runes)} runes: {runes}')

# Les sigils testés pour Support
sigils = optimizer._get_wvw_meta_sigils('support')
print(f'Support testera {len(sigils)} sigils: {sigils}')
"
```

### Test Optimizer DPS (4 runes + 5 sigils)
```bash
poetry run python -c "
from app.agents.build_equipment_optimizer import get_build_optimizer

optimizer = get_build_optimizer()

# DPS
runes = optimizer._get_wvw_meta_runes('dps')
sigils = optimizer._get_wvw_meta_sigils('dps')

print(f'DPS testera {len(runes)} runes: {runes}')
print(f'DPS testera {len(sigils)} sigils: {sigils}')

# Combos possibles
combos = optimizer._generate_sigil_combinations(sigils)
print(f'Total {len(combos)} combinaisons de sigils')
print(f'Total ~{len(runes) * len(combos)} tests pour DPS')
"
```

---

## 5. Relancer le Test Outnumber Squad (Avec Nouvelles Options)

```bash
poetry run python scripts/test_outnumber_squad.py
```

**Ce qui va changer :**
- Avant : Testait **Scholar, Eagle, Nightmare** (3 runes)
- Maintenant : Testera **10 runes** (Scholar, Eagle, Hoelbrak, Strength, Monk, Water, etc.)
- Avant : Testait **Force, Impact, Bloodlust, Air** (4 sigils)
- Maintenant : Testera **10 sigils** (Force, Impact, Bloodlust, Air, Energy, Hydromancy, etc.)

**Résultat attendu :**
```
🏆 HAVOC SQUAD - Optimized for Outnumber WvW

1. Firebrand (Support)
   - Best: Monk + Force + Energy (heal optimized)
   
2. Spellbreaker (DPS)
   - Best: Scholar + Force + Bloodlust (max damage)
   
3. Deadeye (Burst DPS)
   - Best: Scholar + Force + Bloodlust (47k burst!)
   
4. Holosmith (DPS Sustain)
   - Best: Hoelbrak + Force + Air (safer than Scholar)
   
5. Willbender (Mobility DPS)
   - Best: Pack + Force + Energy (mobility focused)
```

---

## 6. Tester le Mode WvW Explicite

### Vérifier le Context WvW
```bash
poetry run python -c "
from app.engine.combat.context import CombatContext

context = CombatContext.create_default(game_mode='WvW')
print(f'Game Mode: {context.game_mode}')
print(f'Might: {context.player_boons.get(\"Might\", 0)} stacks')
print(f'Fury: {\"Fury\" in context.player_boons}')
print(f'Target Armor: {context.target_armor} (Heavy)')
"
```

### Créer un Context Custom
```bash
poetry run python -c "
from app.engine.combat.context import CombatContext

# Context pour roaming (moins de boons)
context = CombatContext.create_default(might_stacks=10, fury=False, game_mode='WvW')
context.add_condition_to_target('Vulnerability', 5)

print(f'Game Mode: {context.game_mode}')
print(f'Might: {context.player_boons.get(\"Might\", 0)} stacks')
print(f'Fury: {\"Fury\" in context.player_boons}')
print(f'Target Vuln: {context.target_conditions.get(\"Vulnerability\", 0)} stacks')
"
```

---

## 7. Intégrer LangChain avec Mistral (Function Calling)

### Setup Mistral avec Tools
```bash
poetry run python -c "
from langchain_ollama import ChatOllama
from app.agents.tools.web_search import get_langchain_tools

# Mistral local avec tools
llm = ChatOllama(model='mistral')
tools = get_langchain_tools()

print(f'Mistral a maintenant {len(tools)} tools:')
for tool in tools:
    print(f'  - {tool.name}: {tool.description[:50]}...')
"
```

### Laisser Mistral Utiliser les Tools
```python
# Créer un script test_mistral_tools.py
from langchain_ollama import ChatOllama
from app.agents.tools.web_search import get_langchain_tools

llm = ChatOllama(model="mistral")
tools = get_langchain_tools()
llm_with_tools = llm.bind_tools(tools)

# Mistral décide automatiquement d'utiliser web_search
response = llm_with_tools.invoke("What is the current WvW meta for Necromancer?")
print(response)
```

---

## 8. Vérifier Tout Rapidement

### Script de Vérification Complète
```bash
poetry run python -c "
print('=== VERIFICATION COMPLETE ===')

# 1. Registry
from app.engine.gear.registry import RUNE_REGISTRY, SIGIL_REGISTRY
print(f'✅ Runes: {len(RUNE_REGISTRY)} disponibles')
print(f'✅ Sigils: {len(SIGIL_REGISTRY)} disponibles')

# 2. Traits Parser
from app.engine.parsers import TraitParser
parser = TraitParser()
print(f'✅ Traits Parser: OK')

# 3. Web Search
from app.agents.tools import create_web_search_tool
search = create_web_search_tool()
print(f'✅ Web Search: {'Available' if search.is_available() else 'Not installed'}')

# 4. WvW Mode
from app.engine.combat.context import CombatContext
context = CombatContext.create_default()
print(f'✅ WvW Mode: {context.game_mode}')

# 5. Optimizer
from app.agents.build_equipment_optimizer import get_build_optimizer
optimizer = get_build_optimizer()
dps_runes = optimizer._get_wvw_meta_runes('dps')
print(f'✅ Optimizer DPS runes: {len(dps_runes)} options')

print('')
print('🎉 TOUT EST OPERATIONNEL !')
"
```

---

## 9. Commandes de Débogage

### Si LangChain ne s'installe pas
```bash
# Vérifier la version de Python
python --version  # Doit être >= 3.11

# Installer manuellement
pip install langchain langchain-community duckduckgo-search

# Ou forcer Poetry
poetry add langchain@latest langchain-community@latest duckduckgo-search@latest
```

### Si DuckDuckGo ne marche pas
```bash
# Tester la lib directement
poetry run python -c "
from duckduckgo_search import DDGS

with DDGS() as ddgs:
    results = ddgs.text('gw2 wvw meta 2024', max_results=3)
    for r in results:
        print(r['title'])
"
```

### Si le Traits Parser échoue
```bash
# Vérifier qu'il retourne bien des modifiers
poetry run python -c "
from app.engine.parsers import TraitParser

parser = TraitParser()
trait = {'name': 'Test', 'description': '+10% damage', 'facts': []}
mods = parser.parse_trait(trait)
print(f'Parsed {len(mods)} modifiers')
assert len(mods) > 0, 'Parser should find modifiers'
print('✅ Parser fonctionne')
"
```

---

## 10. Utilisation Avancée

### Créer un Agent Custom avec Web Search
```python
# scripts/test_meta_agent.py
from langchain_ollama import ChatOllama
from app.agents.tools import create_gw2_meta_search_tool

# Agent spécialisé meta WvW
llm = ChatOllama(model="mistral")
search_tool = create_gw2_meta_search_tool()

class MetaAgent:
    def __init__(self):
        self.llm = llm
        self.search = search_tool
    
    def find_meta_build(self, profession: str, role: str = "DPS"):
        # Chercher le meta
        search_results = self.search.search_wvw_meta(profession, role)
        
        # Demander à l'IA d'analyser
        prompt = f"""
        Based on these search results about {profession} {role} WvW builds:
        
        {search_results}
        
        Extract the most recommended build (runes, sigils, traits).
        """
        
        analysis = self.llm.invoke(prompt)
        return analysis

# Utilisation
agent = MetaAgent()
result = agent.find_meta_build("Necromancer", "DPS")
print(result)
```

---

## 🎯 Résumé des Commandes Essentielles

```bash
# 1. Installer LangChain (1 fois)
poetry add langchain langchain-community duckduckgo-search

# 2. Tester recherche web
poetry run python -c "from app.agents.tools import search_gw2_meta; print(search_gw2_meta('Guardian', 'Support'))"

# 3. Tester nouvelles runes/sigils
poetry run python -c "from app.engine.gear.registry import RUNE_REGISTRY; print(list(RUNE_REGISTRY.keys()))"

# 4. Tester optimizer amélioré
poetry run python scripts/test_outnumber_squad.py

# 5. Vérifier tout
poetry run python -c "from app.engine.gear.registry import RUNE_REGISTRY; print(f'{len(RUNE_REGISTRY)} runes OK')"
```

---

## ✅ Checklist Finale

- [ ] LangChain installé : `poetry add langchain langchain-community duckduckgo-search`
- [ ] Web search fonctionne : Teste `search_gw2_meta("Guardian", "Support")`
- [ ] 10 runes disponibles : Vérifie `list(RUNE_REGISTRY.keys())`
- [ ] 10 sigils disponibles : Vérifie `list(SIGIL_REGISTRY.keys())`
- [ ] Traits parser OK : Parse un trait de test
- [ ] WvW mode explicite : `CombatContext.game_mode == "WvW"`
- [ ] Optimizer mis à jour : `optimizer._get_wvw_meta_runes("support")` retourne 5 runes

**Tout coché ? → TU ES PRÊT ! 🚀**
