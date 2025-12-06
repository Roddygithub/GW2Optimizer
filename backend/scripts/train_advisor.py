#!/usr/bin/env python
from __future__ import annotations
"""Self-play training script for BuildAdvisorAgent / TeamCommanderAgent.

Usage (from backend/ directory):

    poetry run python scripts/train_advisor.py --iterations 200 --delay 0.1

Le script génère des scénarios WvW aléatoires (roam/zerg/outnumber,
roles variés) et appelle TeamCommanderAgent. À chaque optimisation de slot,
le BuildAdvisorAgent V2 arbitre les presets (via LLM si disponible) et
journalise sa décision via le DataCollector dans `training_data/`.

Ainsi, chaque itération produit potentiellement plusieurs TrainingDatapoint
(type "advisor_decision"), réutilisables plus tard pour du few-shot ou
du fine-tuning AlphaGW2.
"""

import argparse
import asyncio
import random
from typing import List

from app.agents.team_commander_agent import TeamCommanderAgent


MESSAGES: List[str] = [
    # Roam
    "Je veux une petite team roam avec beaucoup de dps et un peu de sustain.",
    "Donne-moi une compo roam agressive avec Scrapper, Reaper et Harbinger.",
    "Compose une team de roam 5 joueurs avec un healer léger et des dps.",
    # Zerg
    "Je veux une compo zerg classique avec stab, heal, boon share et dps.",
    "Fais-moi une compo 15 joueurs pour zerg avec beaucoup de stabilité et de cleanse.",
    # Outnumber
    "Je veux une équipe outnumber très tanky pour tenir en sous-nombre.",
    "Fais-moi une compo 10 joueurs orientée survie pour défendre en outnumber.",
]

MODES: List[str] = ["wvw_roam", "wvw_zerg", "wvw_outnumber"]
EXPERIENCES: List[str] = ["beginner", "intermediate", "expert"]


async def run_iteration(agent: TeamCommanderAgent, iteration: int) -> None:
    """Run a single self-play iteration.

    On laisse TeamCommanderAgent construire une team complète pour un scénario
    donné; les décisions de l'advisor sont automatiquement collectées via le
    DataCollector côté backend.
    """

    mode = random.choice(MODES)
    experience = random.choice(EXPERIENCES)
    message = random.choice(MESSAGES)

    try:
        result = await agent.run(message, experience=experience, mode=mode)
        team_size = sum(len(g.slots) for g in result.groups)
        print(
            f"[{iteration}] mode={mode} exp={experience} msg='{message[:40]}...' "
            f"team_size={team_size} synergy={result.synergy_score}"
        )
    except Exception as e:
        print(f"[{iteration}] ERROR: {e}")


async def main(iterations: int, delay: float) -> None:
    agent = TeamCommanderAgent()

    for i in range(1, iterations + 1):
        await run_iteration(agent, i)
        if delay > 0:
            await asyncio.sleep(delay)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Advisor self-play training script.")
    parser.add_argument(
        "--iterations",
        type=int,
        default=100,
        help="Number of iterations to run (default: 100)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help="Optional delay in seconds between iterations (default: 0.0)",
    )

    args = parser.parse_args()

    try:
        asyncio.run(main(iterations=args.iterations, delay=args.delay))
    except KeyboardInterrupt:
        print("Training interrupted by user (Ctrl-C). Exiting gracefully.")
