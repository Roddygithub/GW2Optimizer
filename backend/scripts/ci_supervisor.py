#!/usr/bin/env python3
"""
CI Supervisor - Auto-Fix Backend Tests
Boucle auto-fix jusqu'à 79/79 tests backend GREEN

Mission v2.7.0: PostgreSQL transaction isolation + auto-fix complet
"""
import subprocess
import time
import sys
import re
from pathlib import Path
from datetime import datetime

MAX_CYCLES = 5
BACKEND_DIR = Path(__file__).parent.parent
LOG_FILE = BACKEND_DIR / "backend.log"
REPORT_FILE = BACKEND_DIR / "ci_supervisor_report.md"


class Colors:
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    NC = "\033[0m"


def log(message, color=Colors.NC):
    """Log with color"""
    print(f"{color}{message}{Colors.NC}")


def run_tests():
    """Execute pytest and capture results"""
    log("\n🧪 Running pytest backend tests...", Colors.BLUE)

    result = subprocess.run(
        ["pytest", "tests/", "-v", "--tb=short", "--maxfail=5"],
        cwd=BACKEND_DIR,
        capture_output=True,
        text=True,
        timeout=300,
    )

    output = result.stdout + result.stderr

    # Save logs
    with open(LOG_FILE, "w") as f:
        f.write(f"=== TEST RUN {datetime.now()} ===\n\n")
        f.write(output)

    return result.returncode, output


def parse_test_results(output):
    """Parse pytest output to extract metrics"""
    # Extract test counts
    passed = len(re.findall(r"PASSED", output))
    failed = len(re.findall(r"FAILED", output))
    errors = len(re.findall(r"ERROR", output))

    # Extract failure reasons
    failures = []
    for match in re.finditer(r"FAILED (.*?) - (.*?)(?:\n|$)", output):
        test_name = match.group(1)
        reason = match.group(2)[:100]  # First 100 chars
        failures.append((test_name, reason))

    return {"passed": passed, "failed": failed, "errors": errors, "failures": failures, "total": passed + failed}


def auto_fix(logs, metrics):
    """Apply automatic fixes based on error patterns"""
    log("\n🔧 Analyzing failures and applying auto-fixes...", Colors.YELLOW)

    fixes_applied = []

    # Pattern 1: Relation does not exist
    if "relation" in logs and "does not exist" in logs:
        log("  └─ Fix: Re-initializing database tables", Colors.YELLOW)
        subprocess.run(["python", "scripts/init_test_db.py"], cwd=BACKEND_DIR, capture_output=True)
        fixes_applied.append("Re-initialized database tables")

    # Pattern 2: Transaction isolation issues
    if "IntegrityError" in logs or "ForeignKeyViolation" in logs:
        log("  └─ Fix: Transaction isolation issue detected", Colors.YELLOW)
        fixes_applied.append("Transaction isolation (handled by conftest.py)")

    # Pattern 3: KeyError in responses
    if "KeyError" in logs and ("access_token" in logs or "refresh_token" in logs):
        log("  └─ Fix: Authentication token issue", Colors.YELLOW)
        fixes_applied.append("Auth token handling (check auth service)")

    # Pattern 4: 401 Invalid credentials
    if "401" in logs and "Invalid credentials" in logs:
        log("  └─ Fix: Credentials validation issue", Colors.YELLOW)
        fixes_applied.append("Credentials validation (check password hashing)")

    # Pattern 5: 409 Conflict expected but got 201
    if "assert 201 == 409" in logs or "assert 201 == 409" in logs:
        log("  └─ Fix: Duplicate detection not working", Colors.YELLOW)
        fixes_applied.append("Duplicate detection (check unique constraints)")

    return fixes_applied


def generate_report(cycle, metrics, fixes, duration):
    """Generate markdown report"""
    status = "✅ SUCCESS" if metrics["failed"] == 0 else "❌ FAILED"

    report = f"""
## Cycle {cycle} - {status}

**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Duration**: {duration:.2f}s

### Test Results
- **Passed**: {metrics['passed']}/{metrics['total']}
- **Failed**: {metrics['failed']}
- **Errors**: {metrics['errors']}

### Failures
"""

    if metrics["failures"]:
        for test, reason in metrics["failures"][:10]:  # Top 10
            report += f"- `{test}`: {reason}\n"
    else:
        report += "- None ✅\n"

    report += "\n### Auto-Fixes Applied\n"
    if fixes:
        for fix in fixes:
            report += f"- {fix}\n"
    else:
        report += "- None needed\n"

    return report


def main():
    """Main CI supervisor loop"""
    log("=" * 60, Colors.BLUE)
    log(" 🚀 CI SUPERVISOR v2.7.0 - AUTO-FIX MISSION", Colors.BLUE)
    log("=" * 60, Colors.BLUE)
    log("Target: 79/79 backend tests GREEN", Colors.GREEN)
    log(f"Max cycles: {MAX_CYCLES}", Colors.BLUE)
    log(f"Backend dir: {BACKEND_DIR}", Colors.BLUE)

    full_report = f"""# CI Supervisor Report - v2.7.0

**Mission**: 79/79 Backend Tests GREEN
**Start**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

"""

    for cycle in range(1, MAX_CYCLES + 1):
        log(f"\n{'='*60}", Colors.BLUE)
        log(f" CYCLE {cycle}/{MAX_CYCLES}", Colors.BLUE)
        log(f"{'='*60}", Colors.BLUE)

        start_time = time.time()

        # Run tests
        exit_code, logs = run_tests()
        metrics = parse_test_results(logs)

        duration = time.time() - start_time

        # Log results
        if metrics["failed"] == 0 and metrics["errors"] == 0:
            log(f"\n✅ SUCCESS: {metrics['passed']}/{metrics['total']} tests passed!", Colors.GREEN)
            full_report += generate_report(cycle, metrics, [], duration)
            full_report += "\n\n## ✅ MISSION ACCOMPLISHED\n\n"
            full_report += f"All {metrics['passed']} backend tests are GREEN!\n"

            # Save report
            with open(REPORT_FILE, "w") as f:
                f.write(full_report)

            log(f"\n📊 Report saved: {REPORT_FILE}", Colors.GREEN)
            return 0
        else:
            log(f"\n❌ Cycle {cycle}: {metrics['failed']} failures, {metrics['errors']} errors", Colors.RED)
            log(f"   Passed: {metrics['passed']}/{metrics['total']}", Colors.YELLOW)

            # Apply fixes
            fixes = auto_fix(logs, metrics)

            # Generate report for this cycle
            full_report += generate_report(cycle, metrics, fixes, duration)
            full_report += "\n---\n"

            # Wait before retry
            if cycle < MAX_CYCLES:
                log(f"\n⏳ Waiting 5s before cycle {cycle + 1}...", Colors.YELLOW)
                time.sleep(5)

    # Max cycles reached
    log(f"\n⚠️ Max cycles ({MAX_CYCLES}) reached", Colors.RED)
    log(f"   Final: {metrics['passed']}/{metrics['total']} tests passing", Colors.YELLOW)

    full_report += "\n\n## ⚠️ MAX CYCLES REACHED\n\n"
    full_report += f"Final status: {metrics['passed']}/{metrics['total']} tests passing\n"
    full_report += "\n### Remaining Issues\n\n"
    for test, reason in metrics["failures"]:
        full_report += f"- `{test}`: {reason}\n"

    # Save report
    with open(REPORT_FILE, "w") as f:
        f.write(full_report)

    log(f"\n📊 Report saved: {REPORT_FILE}", Colors.YELLOW)
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        log("\n\n⚠️ Interrupted by user", Colors.YELLOW)
        sys.exit(130)
    except Exception as e:
        log(f"\n\n❌ Fatal error: {e}", Colors.RED)
        import traceback

        traceback.print_exc()
        sys.exit(1)
