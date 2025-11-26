from app.services.gear_prefix_validator import validate_prefix_registry_against_itemstats


# Liste restreinte de préfixes considérés comme critiques pour le WvW
# (utilisés massivement dans l'optimizer et Team Commander).
CRITICAL_PREFIXES = {
    "Berserker",
    "Marauder",
    "Dragon",
    "Valkyrie",
    "Minstrel",
    "Harrier",
    "Cleric",
    "Magi",
    "Diviner",
    "Soldier",
    "Trailblazer",
    "Dire",
}


def test_validate_prefix_registry_runs() -> None:
    """Smoke test: la validation doit pouvoir s'exécuter sans lever d'exception.

    Ce test NE vérifie pas encore le contenu exact, il garantit seulement que
    le helper peut tourner dans l'environnement de test (fichiers présents,
    JSON parsable, etc.).
    """

    # Lève une exception uniquement si l'accès aux données GW2 pose problème.
    validate_prefix_registry_against_itemstats()
