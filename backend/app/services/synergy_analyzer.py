"""Advanced synergy analysis for builds and teams."""

from typing import Dict, List
from enum import Enum

from app.models.build import Build, Profession, Role
from app.models.team import TeamComposition, TeamSynergy


class BoonType(str, Enum):
    """Boon types in GW2."""

    MIGHT = "might"
    FURY = "fury"
    QUICKNESS = "quickness"
    ALACRITY = "alacrity"
    PROTECTION = "protection"
    REGENERATION = "regeneration"
    VIGOR = "vigor"
    SWIFTNESS = "swiftness"
    AEGIS = "aegis"
    STABILITY = "stability"
    RESISTANCE = "resistance"


class SynergyAnalyzer:
    """Analyzes synergies between builds and in teams."""

    # Profession boon generation capabilities
    BOON_PROVIDERS: Dict[Profession, List[BoonType]] = {
        Profession.GUARDIAN: [
            BoonType.AEGIS,
            BoonType.PROTECTION,
            BoonType.STABILITY,
            BoonType.QUICKNESS,
            BoonType.MIGHT,
            BoonType.FURY,
        ],
        Profession.REVENANT: [
            BoonType.ALACRITY,
            BoonType.MIGHT,
            BoonType.PROTECTION,
            BoonType.FURY,
            BoonType.STABILITY,
        ],
        Profession.WARRIOR: [BoonType.MIGHT, BoonType.FURY, BoonType.VIGOR],
        Profession.ENGINEER: [
            BoonType.QUICKNESS,
            BoonType.ALACRITY,
            BoonType.MIGHT,
            BoonType.FURY,
            BoonType.PROTECTION,
        ],
        Profession.RANGER: [
            BoonType.MIGHT,
            BoonType.FURY,
            BoonType.REGENERATION,
            BoonType.SWIFTNESS,
            BoonType.ALACRITY,
        ],
        Profession.THIEF: [BoonType.MIGHT, BoonType.FURY, BoonType.VIGOR],
        Profession.ELEMENTALIST: [
            BoonType.MIGHT,
            BoonType.FURY,
            BoonType.PROTECTION,
            BoonType.REGENERATION,
            BoonType.SWIFTNESS,
        ],
        Profession.MESMER: [BoonType.QUICKNESS, BoonType.ALACRITY, BoonType.MIGHT, BoonType.FURY, BoonType.AEGIS],
        Profession.NECROMANCER: [BoonType.MIGHT, BoonType.FURY, BoonType.PROTECTION, BoonType.REGENERATION],
    }

    # Role synergies
    ROLE_SYNERGIES: Dict[Role, List[Role]] = {
        Role.TANK: [Role.SUPPORT, Role.HEALER, Role.BOONSHARE],
        Role.DPS: [Role.BOONSHARE, Role.SUPPORT],
        Role.SUPPORT: [Role.TANK, Role.DPS, Role.HEALER],
        Role.HEALER: [Role.TANK, Role.SUPPORT],
        Role.BOONSHARE: [Role.DPS, Role.TANK],
    }

    def analyze_build(self, build: Build) -> Dict[str, any]:
        """
        Analyze a single build for its capabilities.

        Returns:
            Dictionary with analysis results
        """
        analysis = {
            "boons_provided": self._get_boon_coverage(build),
            "role_effectiveness": self._evaluate_role_effectiveness(build),
            "synergy_potential": self._calculate_synergy_potential(build),
            "strengths": self._identify_strengths(build),
            "weaknesses": self._identify_weaknesses(build),
        }

        return analysis

    def analyze_team(self, team: TeamComposition) -> List[TeamSynergy]:
        """
        Analyze team composition for synergies.

        Returns:
            List of identified synergies
        """
        synergies = []

        if not team.slots:
            return synergies

        # Analyze boon coverage
        boon_synergies = self._analyze_boon_synergies(team)
        synergies.extend(boon_synergies)

        # Analyze role distribution
        role_synergies = self._analyze_role_synergies(team)
        synergies.extend(role_synergies)

        # Analyze profession combinations
        prof_synergies = self._analyze_profession_synergies(team)
        synergies.extend(prof_synergies)

        return synergies

    def calculate_team_score(self, team: TeamComposition) -> Dict[str, float]:
        """
        Calculate detailed scores for a team.

        Returns:
            Dictionary with various scores (0-10)
        """
        scores = {
            "boon_coverage": self._score_boon_coverage(team),
            "role_balance": self._score_role_balance(team),
            "profession_diversity": self._score_profession_diversity(team),
            "synergy_strength": self._score_synergy_strength(team),
            "survivability": self._score_survivability(team),
            "damage_potential": self._score_damage_potential(team),
            "utility": self._score_utility(team),
        }

        # Calculate overall score
        scores["overall"] = sum(scores.values()) / len(scores)

        return scores

    def _get_boon_coverage(self, build: Build) -> List[str]:
        """Get boons that this build can provide."""
        return [boon.value for boon in self.BOON_PROVIDERS.get(build.profession, [])]

    def _evaluate_role_effectiveness(self, build: Build) -> float:
        """Evaluate how effective the build is for its role (0-10)."""
        # Base score
        score = 5.0

        # Adjust based on profession-role synergy
        if build.role == Role.SUPPORT and build.profession in [
            Profession.GUARDIAN,
            Profession.ENGINEER,
            Profession.RANGER,
        ]:
            score += 2.0
        elif build.role == Role.DPS and build.profession in [
            Profession.WARRIOR,
            Profession.THIEF,
            Profession.ELEMENTALIST,
        ]:
            score += 2.0
        elif build.role == Role.TANK and build.profession in [Profession.GUARDIAN, Profession.WARRIOR]:
            score += 2.0

        return min(10.0, score)

    def _calculate_synergy_potential(self, build: Build) -> float:
        """Calculate synergy potential with other builds (0-10)."""
        # Builds with more boon generation have higher synergy potential
        boon_count = len(self.BOON_PROVIDERS.get(build.profession, []))
        return min(10.0, boon_count * 1.5)

    def _identify_strengths(self, build: Build) -> List[str]:
        """Identify build strengths."""
        strengths = []

        boons = self.BOON_PROVIDERS.get(build.profession, [])

        if BoonType.QUICKNESS in boons or BoonType.ALACRITY in boons:
            strengths.append("Provides critical boons (Quickness/Alacrity)")

        if BoonType.STABILITY in boons:
            strengths.append("Provides Stability (CC immunity)")

        if BoonType.PROTECTION in boons and BoonType.AEGIS in boons:
            strengths.append("Strong defensive support")

        if len(boons) >= 5:
            strengths.append("Versatile boon coverage")

        return strengths

    def _identify_weaknesses(self, build: Build) -> List[str]:
        """Identify build weaknesses."""
        weaknesses = []

        boons = self.BOON_PROVIDERS.get(build.profession, [])

        if BoonType.QUICKNESS not in boons and BoonType.ALACRITY not in boons:
            weaknesses.append("No critical boon generation")

        if len(boons) < 3:
            weaknesses.append("Limited boon support")

        if build.role == Role.DPS and build.profession == Profession.NECROMANCER:
            weaknesses.append("Lower mobility in WvW")

        return weaknesses

    def _analyze_boon_synergies(self, team: TeamComposition) -> List[TeamSynergy]:
        """Analyze boon coverage synergies."""
        synergies = []

        # Count boon providers
        boon_coverage: Dict[BoonType, List[int]] = {}

        for slot in team.slots:
            boons = self.BOON_PROVIDERS.get(slot.build.profession, [])
            for boon in boons:
                if boon not in boon_coverage:
                    boon_coverage[boon] = []
                boon_coverage[boon].append(slot.slot_number)

        # Check critical boons
        critical_boons = [BoonType.QUICKNESS, BoonType.ALACRITY, BoonType.MIGHT, BoonType.FURY]
        covered_critical = [b for b in critical_boons if b in boon_coverage]

        if len(covered_critical) >= 3:
            synergies.append(
                TeamSynergy(
                    synergy_type="boons",
                    description=f"Excellent boon coverage: {', '.join(b.value for b in covered_critical)}",
                    involved_slots=[s for slots in boon_coverage.values() for s in slots],
                    strength=9.0,
                )
            )

        return synergies

    def _analyze_role_synergies(self, team: TeamComposition) -> List[TeamSynergy]:
        """Analyze role distribution synergies."""
        synergies = []

        # Count roles
        role_counts: Dict[Role, int] = {}
        for slot in team.slots:
            role = slot.build.role
            role_counts[role] = role_counts.get(role, 0) + 1

        # Check for balanced composition
        has_tank = role_counts.get(Role.TANK, 0) > 0
        has_support = role_counts.get(Role.SUPPORT, 0) > 0 or role_counts.get(Role.HEALER, 0) > 0
        has_dps = role_counts.get(Role.DPS, 0) >= team.team_size * 0.5

        if has_tank and has_support and has_dps:
            synergies.append(
                TeamSynergy(
                    synergy_type="roles",
                    description="Balanced role distribution (Tank, Support, DPS)",
                    involved_slots=list(range(len(team.slots))),
                    strength=8.5,
                )
            )

        return synergies

    def _analyze_profession_synergies(self, team: TeamComposition) -> List[TeamSynergy]:
        """Analyze profession combination synergies."""
        synergies = []

        # Count professions
        prof_counts: Dict[Profession, int] = {}
        for slot in team.slots:
            prof = slot.build.profession
            prof_counts[prof] = prof_counts.get(prof, 0) + 1

        # Check for good diversity
        if len(prof_counts) >= min(5, team.team_size):
            synergies.append(
                TeamSynergy(
                    synergy_type="diversity",
                    description=f"Good profession diversity ({len(prof_counts)} different professions)",
                    involved_slots=list(range(len(team.slots))),
                    strength=7.5,
                )
            )

        return synergies

    def _score_boon_coverage(self, team: TeamComposition) -> float:
        """Score boon coverage (0-10)."""
        if not team.slots:
            return 0.0

        # Check which critical boons are covered
        critical_boons = [
            BoonType.QUICKNESS,
            BoonType.ALACRITY,
            BoonType.MIGHT,
            BoonType.FURY,
            BoonType.PROTECTION,
            BoonType.STABILITY,
        ]

        covered = set()
        for slot in team.slots:
            boons = self.BOON_PROVIDERS.get(slot.build.profession, [])
            covered.update(boons)

        covered_critical = [b for b in critical_boons if b in covered]
        score = (len(covered_critical) / len(critical_boons)) * 10

        return min(10.0, score)

    def _score_role_balance(self, team: TeamComposition) -> float:
        """Score role balance (0-10)."""
        if not team.slots:
            return 0.0

        role_counts: Dict[Role, int] = {}
        for slot in team.slots:
            role = slot.build.role
            role_counts[role] = role_counts.get(role, 0) + 1

        # Ideal: 10-20% support, 10-20% tank, 60-80% DPS
        total = len(team.slots)
        support_ratio = (role_counts.get(Role.SUPPORT, 0) + role_counts.get(Role.HEALER, 0)) / total
        tank_ratio = role_counts.get(Role.TANK, 0) / total
        dps_ratio = role_counts.get(Role.DPS, 0) / total

        score = 10.0
        if support_ratio < 0.1 or support_ratio > 0.3:
            score -= 2.0
        if tank_ratio < 0.05 or tank_ratio > 0.2:
            score -= 2.0
        if dps_ratio < 0.5 or dps_ratio > 0.85:
            score -= 2.0

        return max(0.0, score)

    def _score_profession_diversity(self, team: TeamComposition) -> float:
        """Score profession diversity (0-10)."""
        if not team.slots:
            return 0.0

        prof_counts: Dict[Profession, int] = {}
        for slot in team.slots:
            prof = slot.build.profession
            prof_counts[prof] = prof_counts.get(prof, 0) + 1

        # More diversity = better (up to a point)
        diversity = len(prof_counts)
        max_diversity = min(9, team.team_size)  # 9 professions max

        return (diversity / max_diversity) * 10

    def _score_synergy_strength(self, team: TeamComposition) -> float:
        """Score overall synergy strength (0-10)."""
        synergies = self.analyze_team(team)

        if not synergies:
            return 5.0

        avg_strength = sum(s.strength for s in synergies) / len(synergies)
        return avg_strength

    def _score_survivability(self, team: TeamComposition) -> float:
        """Score team survivability (0-10)."""
        if not team.slots:
            return 0.0

        # Count defensive capabilities
        has_stability = False
        has_protection = False
        has_healing = False

        for slot in team.slots:
            boons = self.BOON_PROVIDERS.get(slot.build.profession, [])
            if BoonType.STABILITY in boons:
                has_stability = True
            if BoonType.PROTECTION in boons:
                has_protection = True
            if slot.build.role in [Role.HEALER, Role.SUPPORT]:
                has_healing = True

        score = 5.0
        if has_stability:
            score += 2.0
        if has_protection:
            score += 1.5
        if has_healing:
            score += 1.5

        return min(10.0, score)

    def _score_damage_potential(self, team: TeamComposition) -> float:
        """Score team damage potential (0-10)."""
        if not team.slots:
            return 0.0

        dps_count = sum(1 for slot in team.slots if slot.build.role == Role.DPS)
        dps_ratio = dps_count / len(team.slots)

        # Ideal: 60-75% DPS
        if 0.6 <= dps_ratio <= 0.75:
            return 9.0
        elif 0.5 <= dps_ratio <= 0.8:
            return 7.5
        else:
            return 5.0

    def _score_utility(self, team: TeamComposition) -> float:
        """Score team utility (CC, cleanse, etc.) (0-10)."""
        # Placeholder - would need more detailed build data
        return 7.0
