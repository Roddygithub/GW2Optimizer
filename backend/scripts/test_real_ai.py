#!/usr/bin/env python3
"""
Test Réel - Mistral AI + GW2 API
Génère une composition d'escouade WvW optimisée avec données live
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.services.gw2_api import get_gw2_api_service
from app.services.mistral_ai import get_mistral_service
from app.api.ai_optimizer import validate_composition


class Colors:
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    MAGENTA = "\033[0;35m"
    NC = "\033[0m"


def log(message, color=Colors.NC):
    """Log with color"""
    print(f"{color}{message}{Colors.NC}")


async def test_real_ai_optimization():
    """Execute real AI team optimization test"""

    log("=" * 80, Colors.BLUE)
    log(" 🔥 TEST RÉEL - MISTRAL AI + GW2 API", Colors.BLUE)
    log("=" * 80, Colors.BLUE)
    log("", Colors.NC)

    log("📋 Test Configuration:", Colors.YELLOW)
    log("  - Team Size: 50 players", Colors.NC)
    log("  - Game Mode: Zerg (WvW)", Colors.NC)
    log("  - Data Source: Live GW2 API + Mistral AI", Colors.NC)
    log("  - Focus: Balanced composition", Colors.NC)
    log("", Colors.NC)

    start_time = datetime.utcnow()

    # Step 1: Fetch live WvW data
    log("📡 Step 1: Fetching live WvW data from GW2 API...", Colors.BLUE)
    gw2_service = get_gw2_api_service()

    try:
        wvw_data = await gw2_service.fetch_live_wvw_data()

        if wvw_data.get("status") == "success":
            log("  ✅ WvW data fetched successfully", Colors.GREEN)
            log("  - Matches: {}".format(len(wvw_data.get('matches', []))), Colors.NC)
            log("  - Objectives: {}".format(len(wvw_data.get('objectives', []))), Colors.NC)
        else:
            log("  ⚠️ WvW data fetch failed, using fallback", Colors.YELLOW)
            wvw_data = {}
    except Exception as e:
        log("  ⚠️ Error fetching WvW data: {}".format(str(e)), Colors.YELLOW)
        wvw_data = {}
    finally:
        await gw2_service.close()

    log("", Colors.NC)

    # Step 2: Generate team composition with Mistral AI
    log("🤖 Step 2: Generating team composition with Mistral AI...", Colors.BLUE)
    mistral_service = get_mistral_service()

    try:
        composition = await mistral_service.generate_team_composition(wvw_data=wvw_data, team_size=50, game_mode="zerg")

        log("  ✅ Team composition generated", Colors.GREEN)
        log("  - Name: {}".format(composition.get('name', 'Unknown')), Colors.NC)
        log("  - Size: {} players".format(composition.get('size', 0)), Colors.NC)
        log("  - Source: {}".format(composition.get('source', 'Unknown')), Colors.NC)
        log("  - Model: {}".format(composition.get('model', 'Unknown')), Colors.NC)
    except Exception as e:
        log("  ❌ Error generating composition: {}".format(str(e)), Colors.RED)
        return 1
    finally:
        await mistral_service.close()

    log("", Colors.NC)

    # Step 3: Validate composition
    log("✅ Step 3: Validating composition coherence...", Colors.BLUE)
    validation = validate_composition(composition, 50)

    if validation["valid"]:
        log("  ✅ Composition is valid", Colors.GREEN)
    else:
        log("  ⚠️ Composition has issues", Colors.YELLOW)

    if validation["errors"]:
        log("  ❌ Errors:", Colors.RED)
        for error in validation["errors"]:
            log("    - {}".format(error), Colors.RED)

    if validation["warnings"]:
        log("  ⚠️ Warnings:", Colors.YELLOW)
        for warning in validation["warnings"]:
            log("    - {}".format(warning), Colors.YELLOW)

    log("", Colors.NC)

    # Step 4: Display composition
    log("📊 Step 4: Team Composition Details:", Colors.BLUE)
    log("", Colors.NC)

    builds = composition.get("builds", [])
    total_count = sum(build.get("count", 0) for build in builds)

    log("  Total Players: {}/50".format(total_count), Colors.NC)
    log("", Colors.NC)

    log("  Builds:", Colors.YELLOW)
    for build in builds:
        profession = build.get("profession", "Unknown")
        role = build.get("role", "Unknown")
        count = build.get("count", 0)
        priority = build.get("priority", "Unknown")
        description = build.get("description", "")

        log("    • {} ({}): {} players - {} priority".format(profession, role, count, priority), Colors.NC)
        if description:
            log("      → {}".format(description), Colors.NC)

    log("", Colors.NC)

    # Display strategy
    if "strategy" in composition:
        log("  Strategy:", Colors.YELLOW)
        log("    {}".format(composition['strategy']), Colors.NC)
        log("", Colors.NC)

    # Display strengths/weaknesses
    if "strengths" in composition:
        log("  Strengths:", Colors.GREEN)
        for strength in composition["strengths"]:
            log("    ✓ {}".format(strength), Colors.GREEN)

    if "weaknesses" in composition:
        log("  Weaknesses:", Colors.RED)
        for weakness in composition["weaknesses"]:
            log("    ✗ {}".format(weakness), Colors.RED)
        log("", Colors.NC)

    # Step 5: Calculate metrics
    end_time = datetime.utcnow()
    duration = (end_time - start_time).total_seconds()

    log("⏱️ Step 5: Performance Metrics:", Colors.BLUE)
    log("  - Total Duration: {:.2f}s".format(duration), Colors.NC)
    log("  - GW2 API: {}".format('Success' if wvw_data else 'Fallback'), Colors.NC)
    log("  - Mistral AI: {}".format(composition.get('source', 'Unknown')), Colors.NC)
    log("  - Validation: {}".format('✅ Valid' if validation['valid'] else '⚠️ Issues'), Colors.NC)
    log("", Colors.NC)

    # Step 6: Save report
    log("💾 Step 6: Saving report...", Colors.BLUE)

    report_dir = BACKEND_DIR.parent / "reports"
    report_dir.mkdir(exist_ok=True)

    report_data = {
        "timestamp": start_time.isoformat(),
        "test_type": "Real AI Team Optimization",
        "duration_seconds": duration,
        "configuration": {"team_size": 50, "game_mode": "zerg", "focus": "balanced"},
        "wvw_data": {
            "status": wvw_data.get("status", "unavailable"),
            "matches_count": len(wvw_data.get("matches", [])),
            "objectives_count": len(wvw_data.get("objectives", [])),
        },
        "composition": composition,
        "validation": validation,
        "metrics": {
            "total_duration": duration,
            "gw2_api_success": bool(wvw_data),
            "mistral_source": composition.get("source", "unknown"),
            "validation_valid": validation["valid"],
        },
    }

    # Save JSON
    json_path = report_dir / "REAL_AI_TEAM_TEST.json"
    with open(json_path, "w") as f:
        json.dump(report_data, f, indent=2)

    log("  ✅ JSON report saved: {}".format(json_path), Colors.GREEN)

    # Save Markdown
    md_path = report_dir / "REAL_AI_TEAM_TEST.md"
    with open(md_path, "w") as f:
        f.write(generate_markdown_report(report_data))

    log("  ✅ Markdown report saved: {}".format(md_path), Colors.GREEN)
    log("", Colors.NC)

    # Final summary
    log("=" * 80, Colors.BLUE)
    log(" 🎉 TEST COMPLETE", Colors.GREEN)
    log("=" * 80, Colors.BLUE)
    log("", Colors.NC)

    log("✅ Team composition generated successfully", Colors.GREEN)
    log("✅ Reports saved to {}".format(report_dir), Colors.GREEN)
    log("✅ Duration: {:.2f}s".format(duration), Colors.GREEN)

    return 0


def generate_markdown_report(data: dict) -> str:
    """Generate markdown report"""

    composition = data["composition"]
    validation = data["validation"]

    # Format the base template with .format()
    md = """# 🔥 TEST RÉEL - MISTRAL AI + GW2 API

**Date**: {timestamp}
**Duration**: {duration:.2f}s
**Status**: {status}

---

## 📊 CONFIGURATION

- **Team Size**: {team_size} players
- **Game Mode**: {game_mode}
- **Focus**: {focus}

---

## 📡 GW2 API DATA

- **Status**: {gw2_status}
- **Matches**: {matches_count}
- **Objectives**: {objectives_count}

---

## 🤖 TEAM COMPOSITION

### Overview

- **Name**: {name}
- **Size**: {size} players
- **Source**: {source}
- **Model**: {model}

### Builds

""".format(
        timestamp=data['timestamp'],
        duration=data['duration_seconds'],
        status='✅ SUCCESS' if validation['valid'] else '⚠️ ISSUES',
        team_size=data['configuration']['team_size'],
        game_mode=data['configuration']['game_mode'],
        focus=data['configuration']['focus'],
        gw2_status=data['wvw_data']['status'],
        matches_count=data['wvw_data']['matches_count'],
        objectives_count=data['wvw_data']['objectives_count'],
        name=composition.get('name', 'Unknown'),
        size=composition.get('size', 0),
        source=composition.get('source', 'Unknown'),
        model=composition.get('model', 'Unknown')
    )

    # Add builds section
    builds = composition.get("builds", [])
    for build in builds:
        md += """
#### {profession} - {role}

- **Count**: {count} players
- **Priority**: {priority}
- **Description**: {description}
""".format(
            profession=build.get('profession', 'Unknown'),
            role=build.get('role', 'Unknown'),
            count=build.get('count', 0),
            priority=build.get('priority', 'Unknown'),
            description=build.get('description', 'N/A')
        )

    # Add strategy section
    md += """
---

## 📈 STRATEGY

{strategy}

### Strengths

""".format(strategy=composition.get('strategy', 'N/A'))

    # Add strengths
    for strength in composition.get("strengths", []):
        md += "- ✅ {}\n".format(strength)

    # Add weaknesses
    md += "\n### Weaknesses\n\n"
    for weakness in composition.get("weaknesses", []):
        md += "- ⚠️ {}\n".format(weakness)

    # Add validation section
    md += """
---

## ✅ VALIDATION

- **Valid**: {}
- **Errors**: {}
- **Warnings**: {}

### Checks

""".format(
        '✅ Yes' if validation['valid'] else '❌ No',
        len(validation['errors']),
        len(validation['warnings'])
    )

    for check_name, check_data in validation.get("checks", {}).items():
        md += "#### {}\n\n```json\n{}\n```\n\n".format(
            check_name,
            json.dumps(check_data, indent=2)
        )

    if validation["errors"]:
        md += "### Errors\n\n"
        for error in validation["errors"]:
            md += "- ❌ {}\n".format(error)
        md += "\n"

    if validation["warnings"]:
        md += "### Warnings\n\n"
        for warning in validation["warnings"]:
            md += "- ⚠️ {}\n".format(warning)
        md += "\n"

    # Add performance metrics
    md += """---

## ⏱️ PERFORMANCE METRICS

- **Total Duration**: {duration:.2f}s
- **GW2 API Success**: {gw2_status}
- **Mistral Source**: {mistral_source}
- **Validation Valid**: {validation_status}""".format(
        duration=data['metrics']['total_duration'],
        gw2_status='✅ Yes' if data['metrics']['gw2_api_success'] else '❌ No',
        mistral_source=data['metrics']['mistral_source'],
        validation_status='✅ Yes' if data['metrics']['validation_valid'] else '❌ No'
    )

    # Add conclusion
    conclusion = '✅ Test réussi - Composition valide et cohérente' if validation['valid'] else '⚠️ Test complété avec avertissements'
    recommendation = 'Déployer en production' if validation['valid'] and not validation['errors'] else 'Réviser la composition'
    
    md += """
---

## 🎯 CONCLUSION

{conclusion}

**Recommandation**: {recommendation}

---

**Generated**: {timestamp}
**Test Type**: Real AI Team Optimization
**Version**: v3.0.0
""".format(
        conclusion=conclusion,
        recommendation=recommendation,
        timestamp=datetime.utcnow().isoformat()
    )

    return md


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(test_real_ai_optimization())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        log("\n\n⚠️ Interrupted by user", Colors.YELLOW)
        sys.exit(130)
    except Exception as e:
        log(f"\n\n❌ Fatal error: {e}", Colors.RED)
        import traceback

        traceback.print_exc()
        sys.exit(1)
