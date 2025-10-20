"""Snowcrows format exporter."""

import json
from typing import Dict, List
from datetime import datetime

from app.models.build import Build, TraitLine, Skill, Equipment
from app.models.team import TeamComposition


class SnowcrowsExporter:
    """Export builds and teams in Snowcrows format."""

    def export_build_json(self, build: Build) -> Dict:
        """
        Export build to Snowcrows JSON format.
        
        Args:
            build: Build to export
            
        Returns:
            Dictionary in Snowcrows format
        """
        return {
            "name": build.name,
            "profession": build.profession.value,
            "specialization": build.specialization or "Core",
            "traits": self._export_traits(build.trait_lines),
            "skills": self._export_skills(build.skills),
            "equipment": self._export_equipment(build.equipment),
            "metadata": {
                "game_mode": build.game_mode.value,
                "role": build.role.value,
                "source": build.source_type or "gw2optimizer",
                "source_url": str(build.source_url) if build.source_url else None,
                "effectiveness": build.effectiveness,
                "difficulty": build.difficulty,
                "exported_at": datetime.utcnow().isoformat(),
            },
            "description": build.description or "",
            "playstyle": build.playstyle or "",
            "synergies": build.synergies,
            "counters": build.counters,
        }

    def export_build_html(self, build: Build) -> str:
        """
        Export build to Snowcrows-style HTML.
        
        Args:
            build: Build to export
            
        Returns:
            HTML string
        """
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{build.name} - {build.profession.value}</title>
    <style>
        {self._get_snowcrows_css()}
    </style>
</head>
<body>
    <div class="build-container">
        <header class="build-header">
            <h1>{build.name}</h1>
            <div class="build-meta">
                <span class="profession">{build.profession.value}</span>
                <span class="specialization">{build.specialization or 'Core'}</span>
                <span class="role">{build.role.value}</span>
                <span class="game-mode">{build.game_mode.value}</span>
            </div>
        </header>

        <section class="build-section">
            <h2>Traits</h2>
            <div class="trait-lines">
                {self._render_trait_lines_html(build.trait_lines)}
            </div>
        </section>

        <section class="build-section">
            <h2>Skills</h2>
            <div class="skills">
                {self._render_skills_html(build.skills)}
            </div>
        </section>

        <section class="build-section">
            <h2>Equipment</h2>
            <div class="equipment">
                {self._render_equipment_html(build.equipment)}
            </div>
        </section>

        {self._render_description_html(build)}
        
        <footer class="build-footer">
            <p>Exported from GW2Optimizer</p>
            <p>Source: {build.source_type or 'AI Generated'}</p>
        </footer>
    </div>
</body>
</html>"""
        return html

    def export_team_json(self, team: TeamComposition) -> Dict:
        """
        Export team composition to JSON.
        
        Args:
            team: Team to export
            
        Returns:
            Dictionary with team data
        """
        return {
            "name": team.name,
            "game_mode": team.game_mode.value,
            "team_size": team.team_size,
            "slots": [
                {
                    "slot_number": slot.slot_number,
                    "player_name": slot.player_name,
                    "priority": slot.priority,
                    "build": self.export_build_json(slot.build),
                }
                for slot in team.slots
            ],
            "synergies": [
                {
                    "type": syn.synergy_type,
                    "description": syn.description,
                    "involved_slots": syn.involved_slots,
                    "strength": syn.strength,
                }
                for syn in team.synergies
            ],
            "strengths": team.strengths,
            "weaknesses": team.weaknesses,
            "overall_rating": team.overall_rating,
            "metadata": {
                "created_by": team.created_by,
                "exported_at": datetime.utcnow().isoformat(),
            },
        }

    def _export_traits(self, trait_lines: List[TraitLine]) -> List[Dict]:
        """Export trait lines."""
        return [
            {
                "id": tl.id,
                "name": tl.name,
                "traits": tl.traits,
            }
            for tl in trait_lines
        ]

    def _export_skills(self, skills: List[Skill]) -> List[Dict]:
        """Export skills."""
        return [
            {
                "slot": skill.slot,
                "id": skill.id,
                "name": skill.name,
            }
            for skill in skills
        ]

    def _export_equipment(self, equipment: List[Equipment]) -> List[Dict]:
        """Export equipment."""
        return [
            {
                "slot": eq.slot,
                "id": eq.id,
                "name": eq.name,
                "stats": eq.stats,
                "rune_or_sigil": eq.rune_or_sigil,
            }
            for eq in equipment
        ]

    def _get_snowcrows_css(self) -> str:
        """Get Snowcrows-style CSS."""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%);
            color: #f1f5f9;
            padding: 20px;
            line-height: 1.6;
        }
        
        .build-container {
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(15, 23, 42, 0.9);
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
        }
        
        .build-header {
            border-bottom: 3px solid #c89b3c;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        
        .build-header h1 {
            color: #c89b3c;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .build-meta {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }
        
        .build-meta span {
            background: rgba(200, 155, 60, 0.2);
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            border: 1px solid #c89b3c;
        }
        
        .build-section {
            margin-bottom: 30px;
        }
        
        .build-section h2 {
            color: #c89b3c;
            font-size: 1.8em;
            margin-bottom: 15px;
            border-left: 4px solid #c89b3c;
            padding-left: 15px;
        }
        
        .trait-lines, .skills, .equipment {
            display: grid;
            gap: 15px;
        }
        
        .trait-line, .skill, .equipment-item {
            background: rgba(30, 58, 138, 0.3);
            padding: 15px;
            border-radius: 8px;
            border: 1px solid rgba(200, 155, 60, 0.3);
        }
        
        .trait-line h3, .skill h3, .equipment-item h3 {
            color: #93c5fd;
            margin-bottom: 8px;
        }
        
        .description {
            background: rgba(30, 58, 138, 0.2);
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #c89b3c;
            margin-bottom: 20px;
        }
        
        .build-footer {
            text-align: center;
            padding-top: 20px;
            border-top: 1px solid rgba(200, 155, 60, 0.3);
            color: #94a3b8;
            font-size: 0.9em;
        }
        
        .synergies, .counters {
            list-style: none;
            padding-left: 0;
        }
        
        .synergies li, .counters li {
            padding: 8px 0;
            border-bottom: 1px solid rgba(200, 155, 60, 0.1);
        }
        
        .synergies li:before {
            content: "✓ ";
            color: #4ade80;
            font-weight: bold;
        }
        
        .counters li:before {
            content: "✗ ";
            color: #f87171;
            font-weight: bold;
        }
        """

    def _render_trait_lines_html(self, trait_lines: List[TraitLine]) -> str:
        """Render trait lines as HTML."""
        if not trait_lines:
            return "<p>No trait lines specified</p>"
        
        html = ""
        for tl in trait_lines:
            html += f"""
            <div class="trait-line">
                <h3>{tl.name}</h3>
                <p>Traits: {', '.join(map(str, tl.traits)) if tl.traits else 'Not specified'}</p>
            </div>
            """
        return html

    def _render_skills_html(self, skills: List[Skill]) -> str:
        """Render skills as HTML."""
        if not skills:
            return "<p>No skills specified</p>"
        
        html = ""
        for skill in skills:
            html += f"""
            <div class="skill">
                <h3>{skill.slot}</h3>
                <p>{skill.name} (ID: {skill.id})</p>
            </div>
            """
        return html

    def _render_equipment_html(self, equipment: List[Equipment]) -> str:
        """Render equipment as HTML."""
        if not equipment:
            return "<p>No equipment specified</p>"
        
        html = ""
        for eq in equipment:
            html += f"""
            <div class="equipment-item">
                <h3>{eq.slot}</h3>
                <p>{eq.name}</p>
                <p>Stats: {eq.stats or 'Not specified'}</p>
                {f'<p>Rune/Sigil: {eq.rune_or_sigil}</p>' if eq.rune_or_sigil else ''}
            </div>
            """
        return html

    def _render_description_html(self, build: Build) -> str:
        """Render description section."""
        html = ""
        
        if build.description:
            html += f"""
            <section class="build-section">
                <h2>Description</h2>
                <div class="description">
                    <p>{build.description}</p>
                </div>
            </section>
            """
        
        if build.playstyle:
            html += f"""
            <section class="build-section">
                <h2>Playstyle</h2>
                <div class="description">
                    <p>{build.playstyle}</p>
                </div>
            </section>
            """
        
        if build.synergies:
            html += f"""
            <section class="build-section">
                <h2>Synergies</h2>
                <ul class="synergies">
                    {''.join(f'<li>{syn}</li>' for syn in build.synergies)}
                </ul>
            </section>
            """
        
        if build.counters:
            html += f"""
            <section class="build-section">
                <h2>Counters</h2>
                <ul class="counters">
                    {''.join(f'<li>{counter}</li>' for counter in build.counters)}
                </ul>
            </section>
            """
        
        return html
