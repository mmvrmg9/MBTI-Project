"""
simulate.py — Run the MBTI crisis-panel nomination simulation.

Usage:
    python simulate.py                  # interactive scenario menu
    python simulate.py --all            # run every scenario back-to-back
    python simulate.py --scenario pr_disaster   # run one scenario by key

Outputs one CSV per scenario: Most Nominated_<scenario_key>.csv
Requires Ollama running locally with the model set in OLLAMA_MODEL (default: llama3).
"""

import argparse
import csv
import os
import sys
import time
from collections import Counter

from agents import (
    AGENTS,
    SCENARIOS,
    csv_person_label,
    nomination_user_message,
    parse_nominee,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3")
NUM_RUNS     = int(os.environ.get("NUM_RUNS", "20"))
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))

BOLD    = "\033[1m"
RESET   = "\033[0m"
YELLOW  = "\033[93m"
GREEN   = "\033[92m"

# ---------------------------------------------------------------------------
# Scenario selection
# ---------------------------------------------------------------------------

def _scenario_menu() -> list[tuple[str, str, str]]:
    """Prompt the user to choose one or all scenarios interactively."""
    print(f"\n{BOLD}Available crisis scenarios:{RESET}")
    for i, (key, name, brief) in enumerate(SCENARIOS, 1):
        print(f"  {i}. {name}")
        print(f"     {brief[:90]}{'…' if len(brief) > 90 else ''}")
    print(f"  {len(SCENARIOS) + 1}. Run ALL scenarios")

    while True:
        raw = input("\nEnter number: ").strip()
        if raw.isdigit():
            choice = int(raw)
            if 1 <= choice <= len(SCENARIOS):
                return [SCENARIOS[choice - 1]]
            if choice == len(SCENARIOS) + 1:
                return list(SCENARIOS)
        print("Invalid choice, please try again.")


def _resolve_scenarios(args: argparse.Namespace) -> list[tuple[str, str, str]]:
    if args.all:
        return list(SCENARIOS)
    if args.scenario:
        keys = {s[0]: s for s in SCENARIOS}
        if args.scenario not in keys:
            print(f"Unknown scenario key '{args.scenario}'. Valid keys: {', '.join(keys)}", file=sys.stderr)
            sys.exit(1)
        return [keys[args.scenario]]
    return _scenario_menu()


# ---------------------------------------------------------------------------
# Single-scenario simulation
# ---------------------------------------------------------------------------

def run_scenario(scenario: tuple[str, str, str], num_runs: int, model: str) -> None:
    key, name, brief = scenario
    csv_path = os.path.join(SCRIPT_DIR, f"Most Nominated_{key}.csv")
    panel_names = [a.name for a in AGENTS]

    print(f"\n{BOLD}{'=' * 60}{RESET}")
    print(f"{BOLD}SCENARIO: {name}{RESET}")
    print(f"{brief}")
    print(f"{BOLD}{'=' * 60}{RESET}")
    print(f"Model : {model}   Runs : {num_runs}")
    print(f"CSV   : {csv_path}\n")

    # Track totals for the end-of-scenario leaderboard
    tally: Counter[str] = Counter()
    parse_failures = 0

    with open(csv_path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["run", "scenario", "nominated", "nominated_by", "answer"])

        for run in range(1, num_runs + 1):
            print(f"{BOLD}----- Run {run} / {num_runs} -----{RESET}")

            for agent in AGENTS:
                print(f"  {agent.name} is thinking...")
                solo_turn = [{
                    "role": "user",
                    "content": nomination_user_message(agent, AGENTS, brief),
                }]

                reply, err = agent.generate_reply(solo_turn, model)

                if err is not None:
                    print(f"  ERROR ({agent.name}): {err}\n")
                    writer.writerow([
                        run, key, "",
                        csv_person_label(AGENTS, agent.name),
                        f"[error] {err}",
                    ])
                    time.sleep(1)
                    continue

                nominee = parse_nominee(reply, [n for n in panel_names if n != agent.name])
                nominated_label = csv_person_label(AGENTS, nominee) if nominee else ""
                nominator_label = csv_person_label(AGENTS, agent.name)
                writer.writerow([run, key, nominated_label, nominator_label, reply])

                print(f"  {agent.color}{BOLD}{agent.name} ({agent.mbti}):{RESET}")
                # Indent reply lines for readability
                for line in reply.splitlines():
                    print(f"  {agent.color}{line}{RESET}")
                print()

                if nominee:
                    tally[nominated_label] += 1
                else:
                    parse_failures += 1
                    print(f"  {YELLOW}[WARN] Could not parse NOMINEE line.{RESET}\n")

                time.sleep(1)

    # --- End-of-scenario summary ---
    print(f"\n{BOLD}{'=' * 60}{RESET}")
    print(f"{BOLD}RESULTS — {name}{RESET}")
    print(f"{'=' * 60}{RESET}")
    if tally:
        ranked = tally.most_common()
        for rank, (label, count) in enumerate(ranked, 1):
            bar = "█" * count
            print(f"  {rank}. {label:<22} {bar} {count}")
    else:
        print("  No nominations recorded.")
    if parse_failures:
        print(f"\n  {YELLOW}Parse failures: {parse_failures}{RESET}")
    print(f"\n  CSV saved → {csv_path}\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="MBTI Crisis Panel Simulation")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--all", action="store_true", help="Run all scenarios")
    group.add_argument("--scenario", metavar="KEY", help="Run a single scenario by key")
    parser.add_argument("--runs", type=int, default=NUM_RUNS, help=f"Runs per scenario (default {NUM_RUNS})")
    parser.add_argument("--model", default=OLLAMA_MODEL, help=f"Ollama model tag (default {OLLAMA_MODEL})")
    args = parser.parse_args()

    scenarios = _resolve_scenarios(args)

    print(f"\n{BOLD}--- SIMULATION STARTING ---{RESET}")
    print(f"Scenarios : {len(scenarios)}   Runs each : {args.runs}   Model : {args.model}")

    for scenario in scenarios:
        run_scenario(scenario, args.runs, args.model)

    print(f"{BOLD}--- SIMULATION ENDED ---{RESET}\n")


if __name__ == "__main__":
    main()
