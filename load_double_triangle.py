#!/usr/bin/env python3
"""Build a CSV of transforms in log.csv record format.

Commands:
  left -> right   add a transform
  l               save to file
  q               quit
"""

from pathlib import Path
from prompt_maker_cli import PromptMakerConfig

PROMA_DIR = Path(__file__).parent
SEP = ";" * 8
FIELDS = 9


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
    transforms: list[tuple[str, str]] = []

    print("Configured transforms:")
    for i, (left, right) in enumerate(configured, 1):
        print(f"  {i:>2}. {left} -> {right}")
    print("\nType a number, left -> right, or: l=save  q=quit")

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
