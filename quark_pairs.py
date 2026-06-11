#!/usr/bin/env python3
"""Explore the ordered-pair space of the 39 quarks.

With 39 quarks there are exactly 39*38 = 1482 ordered pairs (transforms).
This tool treats that space systematically instead of randomly:

  - every quark gets a role:  T=thing  O=observable  A=action  S=social
  - every pair gets a score from role compatibility (observable->action
    is a natural transform, thing->thing is not)
  - pairs already used anywhere in the repo (doubletriangle CSVs,
    PromptMakerConfig.txt, PromptMakerLog.txt) count as covered
  - suggestions are the highest-scoring pairs nobody has tried yet

Run without arguments for the interactive menu, or use subcommands:
    python quark_pairs.py stats
    python quark_pairs.py suggest --top 10 [--from O --to A] [--shuffle]
    python quark_pairs.py grid
    python quark_pairs.py save --top 5
    python quark_pairs.py eval

Every suggest run is logged to suggestions.log. The eval command is the
downstream evaluation: it reports which suggested pairs were later built
into a doubletriangle CSV (the conversion rate), per role combination —
so the role matrix is tested against what actually gets built.
"""

import argparse
import random
import sys
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
QUARKS_CSV = SCRIPT_DIR / "numbered quarks.csv"
CONFIG_TXT = SCRIPT_DIR / "PromptMakerConfig.txt"
LOG_TXT = SCRIPT_DIR / "PromptMakerLog.txt"
SIXD_DIR = SCRIPT_DIR / "sixd"
SUGGEST_LOG = SCRIPT_DIR / "suggestions.log"

ROLES = {
    "container": "T", "shield": "T", "channel": "T", "support": "T",
    "tool": "T", "food": "T", "data": "T", "nature": "T",
    "radiation": "O", "force": "O", "energy": "O", "time": "O",
    "loc": "O", "event": "O", "problem": "O", "pattern": "O",
    "stat": "O", "normal": "O", "activity": "O",
    "fix": "A", "transport": "A", "drive": "A", "animate": "A",
    "compress": "A", "expand": "A", "waitfor": "A", "increase": "A",
    "sequence": "A", "solve": "A",
    "group": "S", "conflict": "S", "own": "S", "val": "S",
    "pref": "S", "dominate": "S", "transaction": "S", "reward": "S",
    "organization": "S", "contract": "S",
}

ROLE_NAMES = {"T": "thing", "O": "observable", "A": "action", "S": "social"}

# (left role, right role) -> score 0..3; unlisted combinations score 1
ROLE_SCORE = {
    ("O", "A"): 3,  # a signal triggers an action
    ("T", "A"): 3,  # a thing gets acted on (tool -> compress)
    ("O", "S"): 2,  # a signal triggers an organizational response
    ("A", "O"): 2,  # an action changes a measurement
    ("A", "S"): 2,  # an action yields a social outcome
    ("S", "A"): 2,  # a social state triggers an action
    ("T", "T"): 0,  # a thing into a thing is not a transform
}


def load_quarks() -> dict[int, str]:
    quarks = {}
    for line in QUARKS_CSV.read_text(encoding="utf-8").splitlines():
        num, _, name = line.strip().partition(";")
        if num.isdigit() and name.strip():
            quarks[int(num)] = name.strip()
    return quarks


def role(name: str) -> str:
    return ROLES.get(name, "?")


def score(left: str, right: str) -> int:
    return ROLE_SCORE.get((role(left), role(right)), 1)


def scan_triangles(names: set[str]) -> set[tuple[str, str]]:
    """Collect quark pairs built into doubletriangle CSVs."""
    built = set()
    for path in SIXD_DIR.glob("doubletriangle*.csv"):
        for line in path.read_text(encoding="utf-8").splitlines():
            parts = line.split(";")
            if len(parts) >= 5 and parts[2] == "transform":
                left, right = parts[3].strip().casefold(), parts[4].strip().casefold()
                if left in names and right in names and left != right:
                    built.add((left, right))
    return built


def scan_used(names: set[str]) -> set[tuple[str, str]]:
    """Collect quark pairs already used anywhere in the repo."""
    used = set(scan_triangles(names))

    def add(left: str, right: str) -> None:
        left, right = left.strip().casefold(), right.strip().casefold()
        if left in names and right in names and left != right:
            used.add((left, right))

    for path in (CONFIG_TXT, LOG_TXT):
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            if "->" in line:
                left, _, right = line.partition("->")
                left = left.split(",")[-1]  # strip "transform," config prefix
                add(left, right.split("->")[0])

    return used


def all_pairs(quarks: dict[int, str]) -> list[tuple[str, str]]:
    names = list(quarks.values())
    return [(l, r) for l in names for r in names if l != r]


def unseen_ranked(quarks, used, role_from=None, role_to=None):
    pairs = [
        (score(l, r), l, r)
        for l, r in all_pairs(quarks)
        if (l, r) not in used
        and (role_from is None or role(l) == role_from)
        and (role_to is None or role(r) == role_to)
    ]
    pairs.sort(key=lambda p: (-p[0], p[1], p[2]))
    return pairs


def cmd_stats(quarks, used) -> None:
    pairs = all_pairs(quarks)
    total = len(pairs)
    print(f"Quarks: {len(quarks)}   ordered pairs: {total}   used: {len(used)}"
          f"   coverage: {100 * len(used) / total:.1f}%")
    print("\nRole of each quark:")
    for code, label in ROLE_NAMES.items():
        members = sorted(n for n in quarks.values() if role(n) == code)
        print(f"  {code} {label:<11} ({len(members):>2}): {', '.join(members)}")
    print("\nUnseen pairs per score:")
    counts = {}
    for l, r in pairs:
        if (l, r) not in used:
            counts[score(l, r)] = counts.get(score(l, r), 0) + 1
    for s in sorted(counts, reverse=True):
        print(f"  score {s}: {counts[s]:>4} pairs")


def cmd_suggest(quarks, used, top, role_from, role_to, shuffle) -> list[tuple[str, str]]:
    ranked = unseen_ranked(quarks, used, role_from, role_to)
    if shuffle:
        best = ranked[0][0] if ranked else 0
        tier = [p for p in ranked if p[0] == best]
        ranked = random.sample(tier, min(top, len(tier)))
    chosen = ranked[:top]
    num = {name: n for n, name in quarks.items()}
    for s, l, r in chosen:
        print(f"  score {s}  [{role(l)}->{role(r)}]  {l} -> {r}"
              f"   (k {num[l]} {num[r]})")
    if chosen:
        already = read_suggestions().keys()
        today = date.today().isoformat()
        with SUGGEST_LOG.open("a", encoding="utf-8") as f:
            for s, l, r in chosen:
                if (l, r) not in already:
                    f.write(f"{today};{l};{r};{s}\n")
    if not chosen:
        print("  (no unseen pairs match)")
    return [(l, r) for _, l, r in chosen]


def read_suggestions() -> dict[tuple[str, str], tuple[str, int]]:
    """Pair -> (first suggested date, score) from suggestions.log."""
    suggestions = {}
    if not SUGGEST_LOG.exists():
        return suggestions
    for line in SUGGEST_LOG.read_text(encoding="utf-8").splitlines():
        parts = line.strip().split(";")
        if len(parts) == 4:
            day, left, right, s = parts
            if (left, right) not in suggestions:
                suggestions[(left, right)] = (day, int(s) if s.isdigit() else 1)
    return suggestions


def cmd_eval(quarks) -> None:
    """Downstream eval: which suggested pairs got built into a triangle?"""
    suggestions = read_suggestions()
    if not suggestions:
        print(f"No suggestions logged yet ({SUGGEST_LOG.name} is empty).")
        print("Run suggest a few times, build triangles, then come back.")
        return
    built = scan_triangles({n.casefold() for n in quarks.values()})
    today = date.today()

    converted, pending = [], []
    for (l, r), (day, s) in suggestions.items():
        days = (today - date.fromisoformat(day)).days
        (converted if (l, r) in built else pending).append((day, days, s, l, r))

    rate = 100 * len(converted) / len(suggestions)
    print(f"Suggested: {len(suggestions)}   built into a triangle: {len(converted)}"
          f"   conversion: {rate:.0f}%")

    if converted:
        print("\nConverted (suggestion -> triangle):")
        for day, days, s, l, r in sorted(converted):
            print(f"  {day}  score {s}  [{role(l)}->{role(r)}]  {l} -> {r}  ({days} days)")

    combos = {}
    for (l, r), (day, s) in suggestions.items():
        key = f"{role(l)}->{role(r)}"
        hit = (l, r) in built
        sug, conv = combos.get(key, (0, 0))
        combos[key] = (sug + 1, conv + (1 if hit else 0))
    print("\nConversion per role combination (the test of the role matrix):")
    for key, (sug, conv) in sorted(combos.items(), key=lambda kv: -kv[1][1] / kv[1][0]):
        print(f"  {key}  {conv}/{sug}  ({100 * conv / sug:.0f}%)")

    if pending:
        print(f"\nOldest pending ({len(pending)} total):")
        for day, days, s, l, r in sorted(pending)[:5]:
            print(f"  {day}  score {s}  {l} -> {r}  ({days} days waiting)")


def cmd_grid(quarks, used) -> None:
    nums = sorted(quarks)
    print("Pair space: rows = left quark, columns = right quark")
    print("  # = used   . = diagonal   0-3 = score of unseen pair\n")
    header = "                  " + "".join(str(n % 10) for n in nums)
    print(header)
    for ln in nums:
        l = quarks[ln]
        row = []
        for rn in nums:
            r = quarks[rn]
            if ln == rn:
                row.append(".")
            elif (l, r) in used:
                row.append("#")
            else:
                row.append(str(score(l, r)))
        print(f"  {ln:>2} {l:<12}  {''.join(row)}")


def cmd_save(pairs: list[tuple[str, str]]) -> None:
    if not pairs:
        print("Nothing to save.")
        return
    with CONFIG_TXT.open("a", encoding="utf-8") as f:
        for l, r in pairs:
            f.write(f"transform, {l} -> {r}\n")
    print(f"Appended {len(pairs)} transform(s) to {CONFIG_TXT.name}")


def ask_roles() -> tuple[str | None, str | None]:
    raw = input("Filter roles left,right (T/O/A/S, Enter for none): ").strip().upper()
    role_from = role_to = None
    if raw:
        parts = [p.strip() for p in raw.replace(",", " ").split()]
        if len(parts) >= 1 and parts[0] in "TOAS":
            role_from = parts[0]
        if len(parts) >= 2 and parts[1] in "TOAS":
            role_to = parts[1]
    return role_from, role_to


def interactive(quarks, used) -> None:
    print("Quark pairs — 39 quarks, 1482 ordered pairs")
    while True:
        print("\n[s]tats  [g]rid  [n]suggest  [v]suggest+save  [e]val  [q]uit")
        choice = input("Choice: ").strip().casefold()
        if choice == "q":
            return
        if choice == "s":
            cmd_stats(quarks, used)
        elif choice == "g":
            cmd_grid(quarks, used)
        elif choice == "e":
            cmd_eval(quarks)
        elif choice in ("n", "v"):
            raw = input("How many pairs? [10]: ").strip()
            top = int(raw) if raw.isdigit() else 10
            role_from, role_to = ask_roles()
            shuffle = input("Shuffle best tier? [y/N]: ").strip().casefold() in ("y", "yes")
            pairs = cmd_suggest(quarks, used, top, role_from, role_to, shuffle)
            if choice == "v" and pairs:
                if input(f"Append {len(pairs)} to {CONFIG_TXT.name}? [Y/n]: ").strip().casefold() not in ("n", "no"):
                    cmd_save(pairs)
                    used.update(pairs)
        else:
            print("Unknown choice.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("stats", help="coverage of the 1482-pair space")
    for name in ("suggest", "save"):
        p = sub.add_parser(name, help="rank best unseen pairs"
                           + (" and append to PromptMakerConfig.txt" if name == "save" else ""))
        p.add_argument("--top", type=int, default=10)
        p.add_argument("--from", dest="role_from", choices="TOAS", default=None)
        p.add_argument("--to", dest="role_to", choices="TOAS", default=None)
        p.add_argument("--shuffle", action="store_true",
                       help="random picks from the best score tier")
    sub.add_parser("grid", help="39x39 map of used and unseen pairs")
    sub.add_parser("eval", help="conversion rate: suggested pairs that became triangles")
    args = parser.parse_args()

    quarks = load_quarks()
    missing = [n for n in quarks.values() if n not in ROLES]
    if missing:
        print(f"warning: no role for: {', '.join(missing)}", file=sys.stderr)
    used = scan_used({n.casefold() for n in quarks.values()})

    if args.command is None:
        try:
            interactive(quarks, used)
        except (EOFError, KeyboardInterrupt):
            print()
        return 0

    if args.command == "stats":
        cmd_stats(quarks, used)
    elif args.command == "suggest":
        cmd_suggest(quarks, used, args.top, args.role_from, args.role_to, args.shuffle)
    elif args.command == "grid":
        cmd_grid(quarks, used)
    elif args.command == "eval":
        cmd_eval(quarks)
    elif args.command == "save":
        pairs = cmd_suggest(quarks, used, args.top, args.role_from, args.role_to, args.shuffle)
        cmd_save(pairs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
