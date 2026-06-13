#!/usr/bin/env python3
"""Adapt to a problem by combining quarks (README Appendix B).

Four building blocks on top of quark_pairs.py:

  words_to_quarks  - map a problem description onto the 39 quarks
  triangle_score   - score a whole set of wires, not just one pair
  build_triangle   - assemble a candidate double triangle for a problem
  update_weights   - learn the role-combo scores from solved/abandoned outcomes

Run a demo:
    python problem_to_quarks.py "pressure too low, dirt dried on the paint"
"""

import json
import sys
from datetime import date
from pathlib import Path

from quark_pairs import load_quarks, role, score, unseen_ranked, scan_used

SCRIPT_DIR = Path(__file__).parent
MAPPINGS_LOG = SCRIPT_DIR / "mappings.log"
WEIGHTS_JSON = SCRIPT_DIR / "weights.json"

# A handful of everyday words per quark. Extend freely; misses are logged to
# mappings.log so the table grows around the problems people actually bring.
SYNONYMS = {
    # things (T)
    "container": ["box", "tank", "vessel", "bin", "holder"],
    "shield": ["guard", "cover", "protect", "barrier", "shelter"],
    "channel": ["pipe", "duct", "path", "route", "hose"],
    "support": ["stand", "frame", "base", "prop", "mount"],
    "tool": ["device", "instrument", "equipment", "machine", "gear"],
    "food": ["meal", "feed", "nutrient", "fuel", "supply"],
    "data": ["record", "info", "reading", "log", "number"],
    "nature": ["plant", "soil", "weather", "environment", "field"],
    # observables (O)
    "radiation": ["light", "sun", "lux", "heat", "irradiance"],
    "force": ["pressure", "push", "load", "strength", "tension"],
    "energy": ["power", "charge", "voltage", "yield", "watt"],
    "time": ["old", "delay", "dried", "aged", "wait", "late", "duration"],
    "loc": ["place", "position", "location", "where", "spot"],
    "event": ["incident", "trigger", "occurrence", "alarm", "happening"],
    "problem": ["fault", "issue", "defect", "trouble", "failure"],
    "pattern": ["trend", "shape", "recurring", "regular", "cycle"],
    "stat": ["count", "rate", "level", "measure", "metric", "amount"],
    "normal": ["baseline", "standard", "expected", "usual", "default"],
    "activity": ["work", "action", "hours", "usage", "busy"],
    # actions (A)
    "fix": ["repair", "mend", "correct", "patch", "restore"],
    "transport": ["move", "carry", "ship", "deliver", "haul"],
    "drive": ["motor", "actuate", "spin", "turn", "propel"],
    "animate": ["start", "activate", "wake", "run", "enliven"],
    "compress": ["shrink", "squeeze", "shorten", "pack", "reduce"],
    "expand": ["grow", "stretch", "widen", "scale", "enlarge"],
    "waitfor": ["pause", "hold", "await", "block", "queue"],
    "increase": ["raise", "boost", "more", "amplify", "up"],
    "sequence": ["order", "schedule", "steps", "sort", "chain"],
    "solve": ["resolve", "answer", "settle", "handle", "clear"],
    # social (S)
    "group": ["team", "attendance", "crowd", "meeting", "members"],
    "conflict": ["dispute", "clash", "argument", "tension", "disagreement"],
    "own": ["owner", "belong", "possess", "responsible", "assigned"],
    "val": ["value", "rating", "worth", "score", "opinion"],
    "pref": ["preference", "choice", "favor", "like", "want"],
    "dominate": ["control", "rule", "overpower", "lead", "boss"],
    "transaction": ["sale", "deal", "trade", "exchange", "purchase"],
    "reward": ["thanks", "prize", "bonus", "praise", "recognition"],
    "organization": ["structure", "roster", "role", "rules", "process"],
    "contract": ["agreement", "promise", "deadline", "commitment", "deal"],
}


def words_to_quarks(text: str) -> list[tuple[str, float]]:
    """Map a problem description onto quarks, ranked by hit count.

    Unrecognised words are appended to mappings.log so the table can grow.
    """
    hits: dict[str, float] = {}
    misses: list[str] = []
    for raw in text.casefold().replace(",", " ").split():
        word = raw.strip(".;:!?\"'()")
        if not word:
            continue
        matched = False
        for quark, syns in SYNONYMS.items():
            if word == quark or word in syns:
                hits[quark] = hits.get(quark, 0) + 1
                matched = True
        if not matched and len(word) > 2:
            misses.append(word)
    if misses:
        today = date.today().isoformat()
        with MAPPINGS_LOG.open("a", encoding="utf-8") as f:
            for word in misses:
                f.write(f"{today};{word}\n")
    return sorted(hits.items(), key=lambda kv: (-kv[1], kv[0]))


def triangle_score(wires: list[tuple[str, str]]) -> float:
    """Score a whole set of wires: pair quality, role coverage, low redundancy."""
    if not wires:
        return 0.0
    pair_q = sum(score(l, r) for l, r in wires) / len(wires)
    roles_used = {role(l) for l, _ in wires} | {role(r) for _, r in wires}
    coverage = len(roles_used) / 4              # reward using all of T/O/A/S
    redundancy = 1 - len(set(wires)) / len(wires)   # penalize duplicates
    return pair_q * coverage * (1 - redundancy)


def build_triangle(problem: str, quarks, used, k: int = 5) -> list[tuple[str, str]]:
    """Assemble a candidate double triangle for a problem.

    Each problem quark becomes the observable (left) side of a wire; the best
    unseen action quark is picked for the right side via unseen_ranked().
    """
    seeds = [q for q, _ in words_to_quarks(problem)]
    wires: list[tuple[str, str]] = []
    for left in seeds:
        ranked = unseen_ranked(quarks, used, role(left), "A")
        for s, l, r in ranked:
            if l == left and (l, r) not in wires:
                wires.append((l, r))
                break
        if len(wires) >= k:
            break
    return wires


def load_weights() -> dict[tuple[str, str], float]:
    """Load the learnable role-combo weights from weights.json."""
    if not WEIGHTS_JSON.exists():
        return {}
    raw = json.loads(WEIGHTS_JSON.read_text(encoding="utf-8"))
    return {tuple(k.split("->")): v for k, v in raw.items()}


def save_weights(weights: dict[tuple[str, str], float]) -> None:
    raw = {f"{a}->{b}": v for (a, b), v in weights.items()}
    WEIGHTS_JSON.write_text(json.dumps(raw, indent=2), encoding="utf-8")


def update_weights(wires, solved: bool, weights: dict, lr: float = 0.1) -> dict:
    """Nudge the score of each wire's role-combo up if solved, down if abandoned."""
    for l, r in wires:
        key = (role(l), role(r))
        weights[key] = weights.get(key, 1.0) + lr * (1 if solved else -1)
    return weights


def main(argv: list[str]) -> int:
    problem = " ".join(argv) or "pressure too low, dirt dried on the paint, team morale dropping"
    quarks = load_quarks()
    used = scan_used({n.casefold() for n in quarks.values()})

    print(f"Problem: {problem}\n")
    mapped = words_to_quarks(problem)
    print("Quarks found:")
    for q, n in mapped:
        print(f"  {q:<13} [{role(q)}]  (x{int(n)})")

    wires = build_triangle(problem, quarks, used)
    print("\nCandidate triangle:")
    for l, r in wires:
        print(f"  {l} -> {r}   [{role(l)}->{role(r)}]")
    print(f"\ntriangle_score = {triangle_score(wires):.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
