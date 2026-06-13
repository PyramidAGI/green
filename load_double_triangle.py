#!/usr/bin/env python3
"""Build a CSV of transforms in log.csv record format.

Commands:
  left -> right   add a transform
  N               add configured transform by number
  k               list quarks
  k N M           add quark N -> quark M as a transform
  p <problem>     auto-build transforms from a problem description
  l               save to file
  q               quit
"""

from pathlib import Path
from prompt_maker_cli import PromptMakerConfig
from problem_to_quarks import build_triangle, triangle_score
from quark_pairs import scan_used

PROMA_DIR = Path(__file__).parent
QUARKS_CSV = PROMA_DIR / "numbered quarks.csv"
SEP = ";" * 8
FIELDS = 9


def load_quarks() -> dict[int, str]:
    quarks: dict[int, str] = {}
    for line in QUARKS_CSV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        num, _, name = line.partition(";")
        if num.isdigit():
            quarks[int(num)] = name.strip()
    return quarks


def load_configured_transforms() -> list[tuple[str, str]]:
    config = PromptMakerConfig.load(PROMA_DIR / "PromptMakerConfig.txt")
    result = []
    for t in config.transforms:
        if "->" in t:
            left, _, right = t.partition("->")
            result.append((left.strip(), right.strip()))
    return result



def row(*values: str) -> str:
    fields = list(values) + [""] * (FIELDS - len(values))
    return ";".join(fields[:FIELDS])


def save(transforms: list[tuple[str, str]]) -> None:
    raw = input("Give a number 1-9 to which double triangle you want to write: ").strip()
    if raw not in {str(n) for n in range(1, 10)}:
        print("Invalid number, must be 1-9.")
        return
    out = Path(__file__).parent / "sixd" / f"doubletriangle{raw}.csv"
    lines = [SEP]
    for left, right in transforms:
        lines.append(row("", "c", "transform", left, right))
    lines.append(row("", "q", "sensor"))
    lines.append(row("", "c", "actuator"))
    lines.append(row("", "c", "control"))
    lines.append(row("", "c", "plan"))
    lines.append(row("", "c", "nav"))
    lines.append(SEP)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Saved {len(transforms)} transform(s) to {out}")


def main() -> None:
    configured = load_configured_transforms()
    quarks = load_quarks()
    transforms: list[tuple[str, str]] = []

    print("Configured transforms:")
    for i, (left, right) in enumerate(configured, 1):
        print(f"  {i:>2}. {left} -> {right}")
    print("\nType a number, left -> right, or: k=quarks  k N M=quark transform"
          "  p <problem>=auto-build  l=save  q=quit")

    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not line:
            continue
        if line.casefold() == "q":
            break
        if line.casefold() == "l":
            if transforms:
                save(transforms)
            else:
                print("No transforms to save.")
            continue

        if line.lower() == "p" or line.lower().startswith("p "):
            problem = line[1:].strip()
            if not problem:
                print("  Use: p <problem description>")
                continue
            used = scan_used({n.casefold() for n in quarks.values()})
            wires = build_triangle(problem, quarks, used)
            if not wires:
                print("  No quarks recognised in that problem. Try other words.")
                continue
            for left, right in wires:
                transforms.append((left, right))
                print(f"  [{len(transforms)}] {left} -> {right}")
            print(f"  triangle_score = {triangle_score(wires):.3f}")
            continue

        if line.lower().startswith("k"):
            rest = line[1:].strip()
            if not rest:
                for n, name in sorted(quarks.items()):
                    print(f"  {n:>2}. {name}")
            else:
                parts = rest.split()
                if len(parts) == 2 and all(p.isdigit() for p in parts):
                    ln, rn = int(parts[0]), int(parts[1])
                    if ln in quarks and rn in quarks:
                        left, right = quarks[ln], quarks[rn]
                        transforms.append((left, right))
                        print(f"  [{len(transforms)}] {left} -> {right}")
                    else:
                        print(f"  Unknown quark number(s). Use k to list quarks.")
                else:
                    print("  Use: k  to list quarks, or  k N M  to add quark N -> quark M")
            continue

        if line.isdigit():
            index = int(line) - 1
            if 0 <= index < len(configured):
                left, right = configured[index]
                transforms.append((left, right))
                print(f"  [{len(transforms)}] {left} -> {right}")
            else:
                print(f"  Number out of range (1-{len(configured)}).")
            continue

        if "->" not in line:
            parts = line.split()
            if len(parts) == 2:
                line = f"{parts[0]} -> {parts[1]}"

        if "->" in line:
            left, _, right = line.partition("->")
            left, right = left.strip(), right.strip()
            if left and right:
                transforms.append((left, right))
                print(f"  [{len(transforms)}] {left} -> {right}")
                continue

        print("  Use format:  left -> right  or a number from the list")


if __name__ == "__main__":
    main()
