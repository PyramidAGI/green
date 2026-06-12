#!/usr/bin/env python3
"""Six dots explanation app — CLI edition.

The six dots of six_dots.py, but as an explainer: select a dot and read
a paragraph about what it does in the system.

Commands:
  1-6   select a dot
  n     next dot
  p     previous dot
  a     show all paragraphs
  q     quit
"""

import os
import textwrap

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SIXD_DIR = os.path.join(SCRIPT_DIR, "sixd")

LABELS = ["orchestrator", "causal diagram", "double triangle", "bus", "log", "do"]

PARAGRAPHS = [
    # orchestrator
    "The orchestrator is the coordinator of the system. It holds the map of "
    "which causal diagram connects to which double triangle, so when a "
    "criterion in a diagram trips, the orchestrator knows which triangle "
    "must act. It does not sense and it does not act itself - it routes. "
    "Think of it as the dispatcher: diagnosis comes in from the causal "
    "diagrams, work orders go out to the double triangles, and compressed "
    "sentences about all of it are handed to the bus for distribution.",

    # causal diagram
    "The causal diagram is the why of the system. It holds factors and "
    "criteria: a factor is a possible cause taken from a problem tree, and "
    "a criterion is a measurable threshold that tells you when that factor "
    "is really the problem - 'pressure below 100 bar', 'fewer than 2 "
    "thank-yous per repair'. The criteria force vague complaints into "
    "checkable statements. When a criterion trips it points at one factor, "
    "and that factor points at one transform in a double triangle: "
    "diagnosis selects the wire, the wire executes the fix.",

    # double triangle
    "The double triangle is the do of the system - a small control loop "
    "that can act on the world. It holds a sensor (which may be a light "
    "meter or a survey), an actuator (which may be a motor or a person), "
    "and three guiding rows: control runs the loop, plan holds the "
    "sequence of setpoints over time, and nav switches between plans. Its "
    "transforms are wires in quark vocabulary: 'radiation -> drive' means "
    "the radiation reading continuously drives the motor. The same CSV "
    "format steers a Raspberry Pi greenhouse or a repair cafe.",

    # bus
    "The bus is the messenger of the system. It picks up the compressed "
    "sentences from the orchestrator and distributes information to "
    "whoever needs it. Because every component writes the same record "
    "format - nine semicolon-separated fields, documented in "
    "recordexplain.csv - the bus does not need to understand the content "
    "it carries. Uniform containers, meaning at the edges: that is what "
    "lets one Pi sense while another acts, or a survey answer arrive on "
    "the bus like any lux reading.",

    # log
    "The log is the memory of the system. At the moment there is only one "
    "log, and that is a feature: every transform, prompt, and record lands "
    "in the same place in the same format, so any component can replay "
    "what happened. The log is also where evaluation lives - "
    "suggestions.log records what was proposed, the doubletriangle CSVs "
    "record what was built, and the eval command compares the two. A "
    "system that keeps an honest log can check its own beliefs later.",

    # do
    "The do is the executor of the system. It holds 9 functions that can "
    "be mapped to template_program.py - the part that actually runs. "
    "Where the double triangle describes a control loop as data, the do "
    "is the permanent interpreter that breathes life into it: parse the "
    "triangle, look up each quark in the driver catalog, run the loop. "
    "The do never changes; the behavior files do. That inversion - one "
    "fixed program, many swappable behavior files - is what makes the "
    "system self-organizing rather than reprogrammed.",
]


def load_dot_explain() -> dict[int, str]:
    explain = {}
    path = os.path.join(SIXD_DIR, "dotexplain.csv")
    try:
        with open(path, encoding="utf-8-sig") as f:
            for line in f:
                parts = line.strip().split(";", 1)
                if len(parts) == 2 and parts[0].isdigit():
                    explain[int(parts[0]) - 1] = parts[1].strip()
    except FileNotFoundError:
        pass
    return explain


def show_dots(active: int) -> None:
    print()
    for i, label in enumerate(LABELS):
        marker = "(O)" if i == active else " o "
        print(f"  {marker} {i + 1}. {label}")


def show_dot(index: int, one_liners: dict[int, str]) -> None:
    print(f"\n=== {index + 1}. {LABELS[index]} ===")
    if index in one_liners:
        print(f"[{one_liners[index]}]\n")
    print(textwrap.fill(PARAGRAPHS[index], width=76))


def main() -> None:
    one_liners = load_dot_explain()
    active = 0

    print("Six dots — explanation app")
    print("Type 1-6 to select a dot, n=next, p=previous, a=all, q=quit")
    show_dots(active)
    show_dot(active, one_liners)

    while True:
        try:
            choice = input("\n> ").strip().casefold()
        except (EOFError, KeyboardInterrupt):
            print()
            return

        if choice == "q":
            return
        if choice == "n":
            active = (active + 1) % len(LABELS)
        elif choice == "p":
            active = (active - 1) % len(LABELS)
        elif choice in {"1", "2", "3", "4", "5", "6"}:
            active = int(choice) - 1
        elif choice == "a":
            for i in range(len(LABELS)):
                show_dot(i, one_liners)
            continue
        else:
            print("Use 1-6, n, p, a, or q.")
            continue

        show_dots(active)
        show_dot(active, one_liners)


if __name__ == "__main__":
    main()
