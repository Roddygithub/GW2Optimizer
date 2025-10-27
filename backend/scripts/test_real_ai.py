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
            log(f"  ✅ WvW data fetched successfully", Colors.GREEN)
            log(f"  - Matches: {len(wvw_data.get('matches', []))}", Colors.NC)
            log(f"  - Objectives: {len(wvw_data.get('objectives', []))}", Colors.NC)
        else:
            log(f"  ⚠️ WvW data fetch failed, using fallback", Colors.YELLOW)
            wvw_data = {}
    except Exception as e:
        log(f"  ⚠️ Error fetching WvW data: {str(e)}", Colors.YELLOW)
        wvw_data = {}
    finally:
        await gw2_service.close()

    log("", Colors.NC)

    # Step 2: Generate team composition with Mistral AI
    log("🤖 Step 2: Generating team composition with Mistral AI...", Colors.BLUE)
    mistral_service = get_mistral_service()

    try:
        composition = await mistral_service.generate_team_composition(wvw_data=wvw_data, team_size=50, game_mode="zerg")

        log(f"  ✅ Team composition generated", Colors.GREEN)
        log(f"  - Name: {composition.get('name', 'Unknown')}", Colors.NC)
        log(f"  - Size: {composition.get('size', 0)} players", Colors.NC)
        log(f"  - Source: {composition.get('source', 'Unknown')}", Colors.NC)
        log(f"  - Model: {composition.get('model', 'Unknown')}", Colors.NC)
    except Exception as e:
        log(f"  ❌ Error generating composition: {str(e)}", Colors.RED)
        return 1
    finally:
        await mistral_service.close()

    log("", Colors.NC)

    # Step 3: Validate composition
    log("✅ Step 3: Validating composition coherence...", Colors.BLUE)
    validation = validate_composition(composition, 50)

    if validation["valid"]:
        log(f"  ✅ Composition is valid", Colors.GREEN)
    else:
        log(f"  ⚠️ Composition has issues", Colors.YELLOW)

    if validation["errors"]:
        log(f"  ❌ Errors:", Colors.RED)
        for error in validation["errors"]:
            log(f"    - {error}", Colors.RED)

    if validation["warnings"]:
        log(f"  ⚠️ Warnings:", Colors.YELLOW)
        for warning in validation["warnings"]:
            log(f"    - {warning}", Colors.YELLOW)

    log("", Colors.NC)

    # Step 4: Display composition
    log("📊 Step 4: Team Composition Details:", Colors.BLUE)
    log("", Colors.NC)

    builds = composition.get("builds", [])
    total_count = sum(build.get("count", 0) for build in builds)

    log(f"  Total Players: {total_count}/50", Colors.NC)
    log("", Colors.NC)

    log("  Builds:", Colors.YELLOW)
    for build in builds:
        profession = build.get("profession", "Unknown")
        role = build.get("role", "Unknown")
        count = build.get("count", 0)
        priority = build.get("priority", "Unknown")
        description = build.get("description", "")

        log(f"    • {profession} ({role}): {count} players - {priority} priority", Colors.NC)
        if description:
            log(f"      → {description}", Colors.NC)

    log("", Colors.NC)

    # Display strategy
    if "strategy" in composition:
        log(f"  Strategy:", Colors.YELLOW)
        log(f"    {composition['strategy']}", Colors.NC)
        log("", Colors.NC)

    # Display strengths/weaknesses
    if "strengths" in composition:
        log(f"  Strengths:", Colors.GREEN)
        for strength in composition["strengths"]:
            log(f"    ✓ {strength}", Colors.GREEN)
        log("", Colors.NC)

    if "weaknesses" in composition:
        log(f"  Weaknesses:", Colors.RED)
        for weakness in composition["weaknesses"]:
            log(f"    ✗ {weakness}", Colors.RED)
        log("", Colors.NC)

    # Step 5: Calculate metrics
    end_time = datetime.utcnow()
    duration = (end_time - start_time).total_seconds()

    log("⏱️ Step 5: Performance Metrics:", Colors.BLUE)
    log(f"  - Total Duration: {duration:.2f}s", Colors.NC)
    log(f"  - GW2 API: {'Success' if wvw_data else 'Fallback'}", Colors.NC)
    log(f"  - Mistral AI: {composition.get('source', 'Unknown')}", Colors.NC)
    log(f"  - Validation: {'✅ Valid' if validation['valid'] else '⚠️ Issues'}", Colors.NC)
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

    log(f"  ✅ JSON report saved: {json_path}", Colors.GREEN)

    # Save Markdown
    md_path = report_dir / "REAL_AI_TEAM_TEST.md"
    with open(md_path, "w") as f:
        f.write(generate_markdown_report(report_data))

    log(f"  ✅ Markdown report saved: {md_path}", Colors.GREEN)
    log("", Colors.NC)

    # Final summary
    log("=" * 80, Colors.BLUE)
    log(" 🎉 TEST COMPLETE", Colors.GREEN)
    log("=" * 80, Colors.BLUE)
    log("", Colors.NC)

    log(f"✅ Team composition generated successfully", Colors.GREEN)
    log(f"✅ Reports saved to {report_dir}", Colors.GREEN)
    log(f"✅ Duration: {duration:.2f}s", Colors.GREEN)

    return 0


def generate_markdown_report(data: dict) -> str:
    """Generate markdown report"""

    composition = data["composition"]
    validation = data["validation"]

    md = f"""# 🔥 TEST RÉEL - MISTRAL AI + GW2 API

**Date**: {data['timestamp']}
**Duration**: {data['duration_seconds']:.2f}s
**Status**: {'✅ SUCCESS' if validation['valid'] else '⚠️ ISSUES'}

---

## 📊 CONFIGURATION

- **Team Size**: {data['configuration']['team_size']} players
- **Game Mode**: {data['configuration']['game_mode']}
- **Focus**: {data['configuration']['focus']}

---

## 📡 GW2 API DATA

- **Status**: {data['wvw_data']['status']}
- **Matches**: {data['wvw_data']['matches_count']}
- **Objectives**: {data['wvw_data']['objectives_count']}

---

## 🤖 TEAM COMPOSITION

### Overview

- **Name**: {composition.get('name', 'Unknown')}
- **Size**: {composition.get('size', 0)} players
- **Source**: {composition.get('source', 'Unknown')}
- **Model**: {composition.get('model', 'Unknown')}

### Builds

"""

    builds = composition.get("builds", [])
    for build in builds:
        md += f"""
#### {build.get('profession', 'Unknown')} - {build.get('role', 'Unknown')}

- **Count**: {build.get('count', 0)} players
- **Priority**: {build.get('priority', 'Unknown')}
- **Description**: {build.get('description', 'N/A')}
"""

    md += f"""
---

## 📈 STRATEGY

{composition.get('strategy', 'N/A')}

### Strengths

"""

    for strength in composition.get("strengths", []):
        md += f"- ✅ {strength}\n"

    md += "\n### Weaknesses\n\n"

    for weakness in composition.get("weaknesses", []):
        md += f"- ⚠️ {weakness}\n"

    md += f"""
---

## ✅ VALIDATION

- **Valid**: {'✅ Yes' if validation['valid'] else '❌ No'}
- **Errors**: {len(validation['errors'])}
- **Warnings**: {len(validation['warnings'])}

### Checks

"""

    for check_name, check_data in validation.get("checks", {}).items():
        md += f"#### {check_name}\n\n"
        md += f"```json\n{json.dumps(check_data, indent=2)}\n```\n\n"

    if validation["errors"]:
        md += "### Errors\n\n"
        for error in validation["errors"]:
            md += f"- ❌ {error}\n"
        md += "\n"

    if validation["warnings"]:
        md += "### Warnings\n\n"
        for warning in validation["warnings"]:
            md += f"- ⚠️ {warning}\n"
        md += "\n"

    md += f"""
---

## ⏱️ PERFORMANCE METRICS

- **Total Duration**: {data['metrics']['total_duration']:.2f}s
- **GW2 API Success**: {'✅ Yes' if data['metrics']['gw2_api_success'] else '❌ No'}
- **Mistral Source**: {data['metrics']['mistral_source']}
- **Validation**: {'✅ Valid' if data['metrics']['validation_valid'] else '⚠️ Issues'}

---

## 🎯 CONCLUSION

{'✅ Test réussi - Composition valide et cohérente' if validation['valid'] else '⚠️ Test complété avec avertissements'}

**Recommandation**: {'Déployer en production' if validation['valid'] and not validation['errors'] else 'Réviser la composition'}

---

**Generated**: {datetime.utcnow().isoformat()}
**Test Type**: Real AI Team Optimization
**Version**: v3.0.0
"""

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
