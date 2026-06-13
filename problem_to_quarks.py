#!/usr/bin/env python3
"""Adapt to a problem by combining quarks (README Appendix B).

Four building blocks on top of quark_pairs.py:

  words_to_quarks  - map a problem description onto the 39 quarks
  triangle_score   - score a whole set of wires, not just one pair
  build_triangle   - assemble a candidate double triangle for a problem
  update_weights   - learn the role-combo scores from solved/abandoned outcomes

Run a demo:
    python problem_to_quarks.py "pressure too low, dirt dried on the paint"

Inspect what the weights loop has learned:
    python problem_to_quarks.py eval
"""

import sys
from datetime import date
from pathlib import Path

from quark_pairs import (
    ROLE_SCORE, base_score, load_quarks, load_weights, role, save_weights,
    score, scan_used, unseen_ranked,
)

SCRIPT_DIR = Path(__file__).parent
MAPPINGS_LOG = SCRIPT_DIR / "mappings.log"
OUTCOMES_LOG = SCRIPT_DIR / "outcomes.log"

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
    "problem": ["fault", "issue", "defect", "trouble", "failure", "dirt"],
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
    "val": ["value", "rating", "worth", "score", "opinion", "morale"],
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


def update_weights(wires, solved: bool, weights: dict, lr: float = 0.1) -> dict:
    """Nudge the score of each wire's role-combo up if solved, down if abandoned.

    Unseen combos seed from the static role matrix (base_score) so learning
    builds on the hand-written prior instead of resetting it to 1.0.
    """
    for l, r in wires:
        key = (role(l), role(r))
        weights[key] = weights.get(key, base_score(l, r)) + lr * (1 if solved else -1)
    return weights


def read_outcomes() -> list[tuple[str, str, bool, list[tuple[str, str]]]]:
    """Parse outcomes.log into (date, file, solved, wires) tuples."""
    rows = []
    if not OUTCOMES_LOG.exists():
        return rows
    for line in OUTCOMES_LOG.read_text(encoding="utf-8").splitlines():
        parts = line.strip().split(";")
        if len(parts) != 4:
            continue
        day, name, verdict, raw = parts
        wires = [tuple(w.split("->")) for w in raw.split() if "->" in w]
        rows.append((day, name, verdict == "solved", wires))
    return rows


def cmd_eval() -> None:
    """Report what the weights loop has learned from outcomes.log."""
    outcomes = read_outcomes()
    if not outcomes:
        print(f"No outcomes logged yet ({OUTCOMES_LOG.name} is empty).")
        print("Build triangles with `p <problem>` in load_double_triangle.py,")
        print("save them, and answer the solved/abandoned prompt to feed this.")
        return

    solved = sum(1 for _, _, s, _ in outcomes if s)
    rate = 100 * solved / len(outcomes)
    print(f"Outcomes logged: {len(outcomes)}   solved: {solved}"
          f"   abandoned: {len(outcomes) - solved}   solve rate: {rate:.0f}%")

    # Per role-combo tally from the logged wires.
    combos: dict[str, list[int]] = {}
    for _, _, ok, wires in outcomes:
        for l, r in wires:
            key = f"{role(l)}->{role(r)}"
            sol, tot = combos.get(key, (0, 0))
            combos[key] = (sol + (1 if ok else 0), tot + 1)

    weights = load_weights()
    print("\nRole-combo learning (solved/used  |  base -> learned weight):")
    for key in sorted(combos, key=lambda k: -combos[k][1]):
        sol, tot = combos[key]
        a, b = key.split("->")
        base = ROLE_SCORE.get((a, b), 1)
        learned = weights.get((a, b))
        moved = f"{base} -> {learned:.2f}" if learned is not None else f"{base} (unchanged)"
        print(f"  {key:<7} {sol}/{tot:<3}  |  {moved}")

    print("\nMost recent outcomes:")
    for day, name, ok, wires in outcomes[-5:]:
        verdict = "solved   " if ok else "abandoned"
        print(f"  {day}  {verdict}  {name}  ({' '.join(f'{l}->{r}' for l, r in wires)})")


def main(argv: list[str]) -> int:
    if argv and argv[0] == "eval":
        cmd_eval()
        return 0

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
