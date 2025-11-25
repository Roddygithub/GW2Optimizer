# SPECIFICATION: Ultimate GW2 Combat Engine - Analyse & Améliorations

## 🎯 Analyse de Ta Proposition

### ✅ Points Forts
- Architecture modulaire claire (core/modifiers/aggregator/simulator)
- Système de modifiers générique et extensible
- Séparation logique physique vs modificateurs

### ⚠️ Éléments Manquants Critiques

## 1. BOONS (CRUCIAL - Oublié!)
Les boons sont ESSENTIELS pour les calculs :
- **Might** : +30 Power et +30 Condition Damage **par stack** (max 25)
- **Fury** : +20% Crit Chance
- **Quickness** : +50% vitesse d'attaque (DPS x1.5)
- **Protection** : -33% dégâts reçus (sur la cible = moins de dégâts)
- **Vulnerability** : +1% dégâts reçus par stack (max 25 = +25% damage)

→ **Sans Might, tu rates 750 Power potentiel !**

## 2. FEROCITY (Manquant)
- 15 Ferocity = +1% Crit Damage
- Base Crit Damage = 150%
- Berserker build a ~220% Crit Damage

## 3. WEAPON STRENGTH VARIANCE
- Ce n'est PAS une valeur fixe
- Chaque type d'arme a un **range** (ex: Staff 947-1053)
- Il faut utiliser la valeur moyenne ou simuler le variance

## 4. CONDITIONS SUR LA CIBLE
Conditions = Debuffs qui changent les calculs :
- **Vulnerability** : +1% dégâts par stack (x1.25 à 25 stacks)
- **Protection** : -33% dégâts conditions
- **Cripple/Chill/Immobilize** : Impactent certains traits

## 5. CONDI STACKING
- **Intensity** : Might, Vulnerability (max stacks)
- **Duration** : Burning, Bleeding (s'empilent en temps)

## 6. DAMAGE MULTIPLIERS STACKING
GW2 a 2 types de multiplicateurs :
- **Multiplicatifs** : 1.05 × 1.10 × 1.07 = 1.2348 (+23.48%)
- **Additifs** : Certains sigils/traits stackent additivement

## 7. PROC RATES & ICD
- Sigils ont des **% de chance** de proc (Sigil of Air = 50%)
- **Internal Cooldown** (ex: Sigil Impact = 5s ICD)

## 8. MULTI-HIT SKILLS
- Fireball = 2 hits (direct + explosion)
- Important pour on-hit effects

## 9. COMBO SYSTEM
- Combo Fields + Finishers
- Critique en WvW (Water + Blast = AoE Heal)

## 10. FOOD & UTILITY
- +100 Power, +70 Ferocity, etc.
- +10% Experience (cosmétique mais présent)

---

## 📐 ARCHITECTURE AMÉLIORÉE PROPOSÉE

```
app/engine/
├── core/
│   ├── constants.py         # Armor values, conversion rates, boon values
│   ├── damage.py            # Strike damage (with crit)
│   ├── condition.py         # Condition damage (all types)
│   ├── healing.py           # Healing formulas
│   └── attributes.py        # Stat conversions (Precision->Crit, etc.)
│
├── modifiers/
│   ├── base.py              # Modifier class
│   ├── conditions.py        # Condition evaluators (health%, boons, etc.)
│   ├── registry.py          # Pre-built modifier database
│   └── stacking.py          # Multiplicative vs Additive stacking logic
│
├── combat/
│   ├── boons.py             # Boon effects
│   ├── conditions.py        # Condition effects (debuffs)
│   ├── context.py           # CombatContext (player + target state)
│   └── combo.py             # Combo field system
│
├── gear/
│   ├── stats.py             # Stat combinations (Berserker, Viper, etc.)
│   ├── runes.py             # Rune effects registry
│   ├── sigils.py            # Sigil effects registry (with ICD, proc%)
│   ├── relics.py            # Relic effects
│   └── consumables.py       # Food, Utility, Enhancement
│
├── traits/
│   ├── parser.py            # Parse GW2 API trait JSON
│   ├── effects.py           # Convert trait descriptions to Modifiers
│   └── database.py          # Pre-built trait modifier database
│
└── simulation/
    ├── aggregator.py        # BuildAggregator (sum all stats)
    ├── calculator.py        # DamageCalculator (final math)
    ├── rotation.py          # Skill rotation simulator (DPS over time)
    └── timeline.py          # Combat timeline (buffs, cooldowns)
```

---

## 🔧 FORMULES COMPLÈTES GW2

### Strike Damage (Power)
```
Damage = (WeaponStrength * Power * SkillCoef / TargetArmor) 
         × CritMultiplier 
         × VulnerabilityMult 
         × OtherMultipliers
```

- **CritMultiplier** = 1.0 (non-crit) ou CritDamage% (crit)
- **CritDamage%** = 1.5 + (Ferocity / 1500)
- **VulnerabilityMult** = 1.0 + (Vuln Stacks × 0.01)

### Condition Damage
```
DamagePerTick = (BaseDamage + 0.05 × ConditionDamage) × Stacks
TotalDamage = DamagePerTick × Duration
```

- **Duration** = BaseDuration × (1 + Expertise/1500 + BonusDuration%)

### Crit Chance
```
CritChance = 0.05 + (Precision / 2100) + Fury(0.20 si actif)
Max: 100%
```

### Effective Power (avec Might)
```
EffectivePower = BasePower + (MightStacks × 30)
```

---

## 🎮 EXEMPLE CONCRET

### Build Berserker avec Might et Fury
```python
# Stats de base
power = 2000
precision = 2100
ferocity = 1500

# Boons actifs
might_stacks = 25
has_fury = True

# Calcul
effective_power = 2000 + (25 × 30) = 2750
crit_chance = 0.05 + (2100/2100) + 0.20 = 1.25 → cap à 1.0 (100%)
crit_damage = 1.5 + (1500/1500) = 2.5 (250%)

# Fireball (coef 0.8)
weapon_strength = 1000
target_armor = 2597

base_damage = (1000 × 2750 × 0.8) / 2597 = 847
crit_damage = 847 × 2.5 = 2117

# Avec Sigil of Force (+5%), Trait (+10%)
final_crit = 2117 × 1.05 × 1.10 = 2445

# Avec 25 Vulnerability sur la cible
final_with_vuln = 2445 × 1.25 = 3056 dégâts!
```

---

## 🚨 PRIORITÉS D'IMPLÉMENTATION

### Phase 1 (Core - Indispensable)
1. ✅ `core/damage.py` - Strike damage de base (FAIT)
2. 🔴 `core/attributes.py` - Conversions (Precision, Ferocity, Expertise)
3. 🔴 `core/constants.py` - Toutes les constantes GW2
4. 🔴 `combat/boons.py` - Système de boons (Might, Fury prioritaire)
5. 🔴 `combat/context.py` - CombatContext

### Phase 2 (Modifiers)
6. 🔴 `modifiers/base.py` - Classe Modifier
7. 🔴 `modifiers/conditions.py` - Évaluateurs
8. 🔴 `modifiers/stacking.py` - Logique de stack (mult vs add)

### Phase 3 (Gear)
9. 🔴 `gear/runes.py` - Effets des runes
10. 🔴 `gear/sigils.py` - Effets des sigils (avec ICD)
11. 🔴 `gear/consumables.py` - Food/Utility

### Phase 4 (Advanced)
12. 🔴 `core/condition.py` - Condition damage
13. 🔴 `simulation/aggregator.py` - BuildAggregator
14. 🔴 `simulation/calculator.py` - DamageCalculator final
15. 🔴 `simulation/rotation.py` - Simulation de rotation

---

## 💡 RECOMMANDATIONS

### 1. Database vs Runtime
**Recommandation** : Créer une **database de modifiers pré-construits**
- `gear/runes.py` → dict de tous les effets de runes
- `gear/sigils.py` → dict de tous les effets de sigils
- `traits/database.py` → dict de traits communs

### 2. Validation
Utiliser des **benchmarks GW2 connus** :
- Golem DPS (Snow Crows)
- Comparer tes calculs vs résultats réels

### 3. UI/UX
Afficher un **breakdown détaillé** :
```
Fireball: 2445 dégâts
├─ Base: 847
├─ Crit (100% chance): ×2.5 = 2117
├─ Sigil of Force: ×1.05 = 2223
├─ Trait Fiery Wrath: ×1.10 = 2445
└─ (vs 25 Vuln: 3056)
```

### 4. Performance
- Calculer une fois, réutiliser (cache)
- Ne pas recalculer à chaque frame

---

## ✅ CE QUI CHANGE vs TA SPEC INITIALE

| Aspect | Ta Version | Version Améliorée |
|--------|------------|-------------------|
| Boons | ❌ Absent | ✅ Module dédié |
| Ferocity | ❌ Non mentionné | ✅ Core attribute |
| Vulnerability | ❌ Absent | ✅ Dans conditions |
| ICD Sigils | ❌ Absent | ✅ Avec cooldown |
| Combo System | ❌ Absent | ✅ Module combo |
| Multi-hit | ❌ Absent | ✅ Géré |
| Food/Utility | ❌ Absent | ✅ Module consumables |

---

## 🎯 CONCLUSION

Ta spec est **excellente comme base**, mais il manque :
1. **Boons** (critique !)
2. **Vulnerability** sur la cible
3. **Ferocity** (Crit Damage)
4. **ICD et proc rates**
5. **Food/Utility buffs**

Avec ces ajouts, le moteur sera **complet et précis** ! 🚀
