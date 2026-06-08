#!/usr/bin/env python3
"""Prompt Maker by PNF7 — command-line edition.

A Python CLI conversion of the original WinForms PromptMaker program.

Default data directory:
    ~/Desktop/Proma

Expected optional files:
    PromptMakerConfig.txt
    PromptMakerBackground.txt
    PromptMakerStory.txt
    PromptMakerBlacklist.txt
    sutsil.txt

The program can be used interactively:
    python prompt_maker_cli.py

Or through subcommands:
    python prompt_maker_cli.py analyze
    python prompt_maker_cli.py generate --auto-top-two --sector AI
    python prompt_maker_cli.py blacklist add the and of
    python prompt_maker_cli.py seed --count 3
"""

from __future__ import annotations

import argparse
import os
import random
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence


DEFAULT_INSTRUCTION = (
    "Describe the main goal you want to achieve with respect to the selected "
    "topic/sector.\nMake an app that uses the transforms to explore:"
)
DEFAULT_PHYSICAL_TRANSFORM = (
    "replace, retrain, repair, find, increase, decrease | on, off } improve"
)
WORD_RE = re.compile(r"[^\W_]+(?:['’][^\W_]+)*", re.UNICODE)
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".jpe", ".jfif", ".png", ".bmp", ".gif"}


class PromptMakerError(RuntimeError):
    """Raised for recoverable Prompt Maker errors."""


def default_proma_dir() -> Path:
    """Return the default Proma directory, allowing an environment override."""
    override = os.environ.get("PROMA_DIR")
    if override:
        return Path(override).expanduser()
    return Path.home() / "Desktop" / "Proma"


def read_text(path: Path, default: str = "") -> str:
    try:
        return path.read_text(encoding="utf-8-sig") if path.exists() else default
    except OSError as exc:
        raise PromptMakerError(f"Could not read {path}: {exc}") from exc


def write_text(path: Path, text: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    except OSError as exc:
        raise PromptMakerError(f"Could not write {path}: {exc}") from exc


def parse_config_line(raw_line: str) -> tuple[str, str] | None:
    """Parse either `key,value` (original format) or `key=value`."""
    line = raw_line.strip()
    if not line or line.startswith("#"):
        return None

    comma = line.find(",")
    equals = line.find("=")
    positions = [pos for pos in (comma, equals) if pos >= 0]
    if not positions:
        return None

    split_at = min(positions)
    key = line[:split_at].strip().lower()
    value = line[split_at + 1 :].strip().strip('"').strip()
    if not key or not value:
        return None
    return key, value


@dataclass(slots=True)
class PromptMakerConfig:
    topics: list[str] = field(default_factory=list)
    guardrails: list[str] = field(default_factory=list)
    transforms: list[str] = field(default_factory=list)
    causal_diagrams: list[str] = field(default_factory=list)

    @classmethod
    def load(cls, path: Path) -> "PromptMakerConfig":
        config = cls()
        if not path.exists():
            return config

        try:
            lines = path.read_text(encoding="utf-8-sig").splitlines()
        except OSError as exc:
            raise PromptMakerError(f"Could not read config file {path}: {exc}") from exc

        destinations = {
            "topic": config.topics,
            "guardrail": config.guardrails,
            "transform": config.transforms,
            "causaldiagram": config.causal_diagrams,
            "causal_diagram": config.causal_diagrams,
        }
        for line in lines:
            parsed = parse_config_line(line)
            if parsed is None:
                continue
            key, value = parsed
            destination = destinations.get(key)
            if destination is not None:
                destination.append(value)
        return config


@dataclass
class PromptMaker:
    proma_dir: Path
    config: PromptMakerConfig = field(init=False)
    story: str = field(init=False, default="")
    background: str = field(init=False, default="")
    blacklist: set[str] = field(init=False, default_factory=set)

    sector: str = ""
    guardrail_enabled: bool = False
    guardrail: str = ""
    goal_topic1: str = ""
    subject_topic2: str = ""
    transforms: list[str] = field(default_factory=list)
    causal_plane: str = ""
    abstraction_level: int = 0
    story_image: Path | None = None
    causal_image: Path | None = None
    instruction: str = DEFAULT_INSTRUCTION
    blacklist_dirty: bool = False

    def __post_init__(self) -> None:
        self.proma_dir = self.proma_dir.expanduser().resolve()
        self.config = PromptMakerConfig.load(self.config_path)
        self.reload_files()
        if self.config.causal_diagrams:
            self.causal_plane = self.config.causal_diagrams[0]

    @property
    def config_path(self) -> Path:
        return self.proma_dir / "PromptMakerConfig.txt"

    @property
    def story_path(self) -> Path:
        return self.proma_dir / "PromptMakerStory.txt"

    @property
    def background_path(self) -> Path:
        return self.proma_dir / "PromptMakerBackground.txt"

    @property
    def blacklist_path(self) -> Path:
        return self.proma_dir / "PromptMakerBlacklist.txt"

    @property
    def sutsil_path(self) -> Path:
        return self.proma_dir / "sutsil.txt"

    @property
    def log_path(self) -> Path:
        return self.proma_dir / "PromptMakerLog.txt"

    def reload_files(self) -> None:
        self.story = read_text(self.story_path)
        self.background = read_text(self.background_path)
        self.blacklist = self._load_blacklist()
        self.blacklist_dirty = False

    def _load_blacklist(self) -> set[str]:
        text = read_text(self.blacklist_path)
        result: set[str] = set()
        for line in text.splitlines():
            for item in line.split(","):
                word = item.strip().strip('"').strip().casefold()
                if word:
                    result.add(word)
        return result

    def load_story(self, path: Path) -> None:
        self.story = read_text(path.expanduser().resolve())

    def save_story(self) -> Path:
        write_text(self.story_path, self.story)
        return self.story_path

    def top_words(self, limit: int = 10) -> list[tuple[str, int]]:
        words = (
            match.group(0).casefold()
            for match in WORD_RE.finditer(self.story or "")
        )
        counts = Counter(word for word in words if word and word not in self.blacklist)
        return sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))[:limit]

    def use_top_two(self) -> tuple[str, str]:
        top = self.top_words(2)
        if len(top) < 2:
            raise PromptMakerError("The story contains fewer than two usable words.")
        self.goal_topic1 = top[0][0]
        self.subject_topic2 = top[1][0]
        return self.goal_topic1, self.subject_topic2

    def add_blacklist(self, words: Iterable[str]) -> list[str]:
        added: list[str] = []
        for raw in words:
            word = raw.strip().casefold()
            if word and word not in self.blacklist:
                self.blacklist.add(word)
                added.append(word)
        if added:
            self.blacklist_dirty = True
        return added

    def remove_blacklist(self, words: Iterable[str]) -> list[str]:
        removed: list[str] = []
        for raw in words:
            word = raw.strip().casefold()
            if word in self.blacklist:
                self.blacklist.remove(word)
                removed.append(word)
        if removed:
            self.blacklist_dirty = True
        return removed

    def save_blacklist(self) -> Path:
        content = "".join(f"{word}\n" for word in sorted(self.blacklist))
        write_text(self.blacklist_path, content)
        self.blacklist_dirty = False
        return self.blacklist_path

    def add_transform(self, transform: str) -> None:
        value = transform.strip()
        if value:
            self.transforms.append(value)

    def add_rule(self, left: str, right: str) -> str:
        rule = f"{left.strip()} -> {right.strip()}"
        self.transforms.append(rule)
        return rule

    def remove_transform(self, index: int) -> str:
        if not 0 <= index < len(self.transforms):
            raise PromptMakerError("Transform number is outside the available range.")
        return self.transforms.pop(index)

    def seed_sutton_silver(self, count: int = 1, add: bool = True) -> list[str]:
        lines = [line.strip() for line in read_text(self.sutsil_path).splitlines() if line.strip()]
        if not lines:
            raise PromptMakerError(f"No entries found in {self.sutsil_path}")

        rules: list[str] = []
        for _ in range(max(1, count)):
            left = random.choice(lines)
            right = random.choice(lines)
            rule = f"{left} -> {right}"
            rules.append(rule)
            if add:
                self.transforms.append(rule)
            beep_for_text(left)
            beep_for_text(right)
        return rules

    def set_image(self, path: Path, causal: bool = False) -> Path:
        resolved = path.expanduser().resolve()
        if not resolved.is_file():
            raise PromptMakerError(f"Image does not exist: {resolved}")
        if resolved.suffix.casefold() not in IMAGE_SUFFIXES:
            raise PromptMakerError(f"Unsupported image type: {resolved.suffix or '(none)'}")
        if causal:
            self.causal_image = resolved
        else:
            self.story_image = resolved
        return resolved

    def build_prompt(self) -> str:
        lines: list[str] = [
            "Story:",
            self.story.strip(),
            "",
            self.instruction.strip(),
            "Sector:",
            self.sector,
            "",
        ]

        if self.guardrail_enabled:
            lines.extend(["Guardrails:", self.guardrail, ""])

        lines.extend(
            [
                "Goal/topic1:",
                self.goal_topic1.strip(),
                "Subject/Object/topic2:",
                self.subject_topic2.strip(),
                "",
                "Transforms:",
            ]
        )
        if self.transforms:
            lines.extend(self.transforms)
        lines.append("")

        if self.causal_plane:
            lines.extend(["Causal plane:", self.causal_plane, ""])

        lines.extend(
            [
                "Abstraction level:",
                str(self.abstraction_level),
                "",
                "End of prompt.",
            ]
        )
        return "\n".join(lines)

    def save_prompt(self) -> Path:
        prompt = self.build_prompt()
        header = f"----- {datetime.now():%Y-%m-%d %H:%M:%S} -----\n"
        try:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with self.log_path.open("a", encoding="utf-8") as handle:
                handle.write(header)
                handle.write(prompt)
                handle.write("\n\n")
        except OSError as exc:
            raise PromptMakerError(f"Could not save prompt to {self.log_path}: {exc}") from exc
        return self.log_path


def stable_frequency(text: str) -> int:
    """Return a repeatable frequency from 200 through 1999 Hz."""
    value = 0
    for character in text:
        value = ((value * 31) + ord(character)) & 0xFFFFFFFF
    return 200 + (value % 1800)


def beep_for_text(text: str) -> None:
    """Use Windows beeps when available; remain silent elsewhere."""
    if sys.platform != "win32":
        return
    try:
        import winsound

        winsound.Beep(stable_frequency(text), 250)
    except (ImportError, RuntimeError, OSError):
        return


def choose_from_list(title: str, values: Sequence[str], allow_empty: bool = True) -> str:
    if not values:
        print(f"No {title.lower()} entries are configured.")
        return ""
    print(f"\n{title}:")
    for index, value in enumerate(values, start=1):
        print(f"  {index}. {value}")
    if allow_empty:
        print("  0. None")
    raw = input("Choose a number: ").strip()
    try:
        number = int(raw)
    except ValueError:
        print("Invalid number.")
        return ""
    if allow_empty and number == 0:
        return ""
    if 1 <= number <= len(values):
        return values[number - 1]
    print("Number outside the available range.")
    return ""


def prompt_path(label: str) -> Path | None:
    raw = input(label).strip().strip('"')
    return Path(raw).expanduser() if raw else None


def print_top_words(app: PromptMaker, limit: int = 10) -> None:
    rows = app.top_words(limit)
    print("\nTop words:")
    if not rows:
        print("  (none)")
        return
    for index, (word, count) in enumerate(rows, start=1):
        print(f"  {index:>2}. {word:<24} {count}")


def print_transforms(app: PromptMaker) -> None:
    print("\nTransforms:")
    if not app.transforms:
        print("  (none)")
        return
    for index, transform in enumerate(app.transforms, start=1):
        print(f"  {index:>2}. {transform}")


def print_status(app: PromptMaker) -> None:
    print("\nCurrent state")
    print(f"  Proma folder:       {app.proma_dir}")
    print(f"  Story characters:   {len(app.story)}")
    print(f"  Sector:             {app.sector or '(none)'}")
    guardrail = app.guardrail if app.guardrail_enabled else "(disabled)"
    print(f"  Guardrail:          {guardrail}")
    print(f"  Goal/topic1:        {app.goal_topic1 or '(none)'}")
    print(f"  Subject/topic2:     {app.subject_topic2 or '(none)'}")
    print(f"  Transforms:         {len(app.transforms)}")
    print(f"  Causal plane:       {app.causal_plane or '(none)'}")
    print(f"  Abstraction level:  {app.abstraction_level}")
    print(f"  Story image:        {app.story_image or '(none)'}")
    print(f"  Causal image:       {app.causal_image or '(none)'}")


def edit_blacklist(app: PromptMaker) -> None:
    while True:
        print(f"\nBlacklist ({len(app.blacklist)} words)")
        print("  [l]ist  [a]dd  [r]emove  [s]ave  [b]ack")
        choice = input("Choice: ").strip().casefold()
        if choice == "l":
            print("\n".join(sorted(app.blacklist)) or "(empty)")
        elif choice == "a":
            words = input("Words to add (space or comma separated): ")
            added = app.add_blacklist(re.split(r"[\s,]+", words))
            print("Added: " + (", ".join(added) if added else "nothing"))
        elif choice == "r":
            words = input("Words to remove (space or comma separated): ")
            removed = app.remove_blacklist(re.split(r"[\s,]+", words))
            print("Removed: " + (", ".join(removed) if removed else "nothing"))
        elif choice == "s":
            print(f"Saved to {app.save_blacklist()}")
        elif choice == "b":
            return
        else:
            print("Unknown choice.")


def interactive(app: PromptMaker) -> int:
    print("Prompt Maker by PNF7 — command-line edition")
    print("Website: https://www.pnf7.nl")

    while True:
        print_status(app)
        print(
            """
Actions
  1. Show top words
  2. Use top two words for topic1/topic2
  3. Load story from a file
  4. Select sector
  5. Configure guardrail
  6. Add configured transform
  7. Add scanned transform (left -> right)
  8. Seed Sutton–Silver transform
  9. Show/remove/clear transforms
 10. Select causal plane
 11. Set abstraction level
 12. Manage blacklist
 13. Store story/causal image path
 14. Preview total prompt
 15. Generate and save prompt
  0. Exit
"""
        )
        choice = input("Choice: ").strip()
        try:
            if choice == "0":
                if app.blacklist_dirty:
                    answer = input("Save changed blacklist before exit? [Y/n] ").strip().casefold()
                    if answer not in {"n", "no"}:
                        print(f"Saved to {app.save_blacklist()}")
                return 0
            if choice == "1":
                print_top_words(app)
            elif choice == "2":
                first, second = app.use_top_two()
                print(f"topic1={first}; topic2={second}")
            elif choice == "3":
                path = prompt_path("Story file path: ")
                if path:
                    app.load_story(path)
                    print(f"Loaded {len(app.story)} characters from {path.resolve()}")
                    print_top_words(app)
            elif choice == "4":
                app.sector = choose_from_list("Sectors", app.config.topics)
            elif choice == "5":
                enabled = input("Enable guardrails? [y/N] ").strip().casefold() in {"y", "yes"}
                app.guardrail_enabled = enabled
                app.guardrail = (
                    choose_from_list("Guardrails", app.config.guardrails) if enabled else ""
                )
            elif choice == "6":
                transform = choose_from_list("Configured transforms", app.config.transforms)
                app.add_transform(transform)
            elif choice == "7":
                left = input("Left: ")
                right = input("Right: ")
                print(f"Added: {app.add_rule(left, right)}")
            elif choice == "8":
                rules = app.seed_sutton_silver()
                print("Added: " + rules[0])
            elif choice == "9":
                print_transforms(app)
                action = input("[r]emove, [c]lear, or Enter to keep: ").strip().casefold()
                if action == "r":
                    number = int(input("Transform number: "))
                    print(f"Removed: {app.remove_transform(number - 1)}")
                elif action == "c":
                    app.transforms.clear()
                    print("Transforms cleared.")
            elif choice == "10":
                app.causal_plane = choose_from_list(
                    "Causal planes", app.config.causal_diagrams
                )
            elif choice == "11":
                app.abstraction_level = int(input("Abstraction level: ").strip())
            elif choice == "12":
                edit_blacklist(app)
            elif choice == "13":
                causal = input("Is this the causal-diagram image? [y/N] ").strip().casefold() in {"y", "yes"}
                path = prompt_path("Image path: ")
                if path:
                    print(f"Stored: {app.set_image(path, causal=causal)}")
            elif choice == "14":
                print("\n" + app.build_prompt())
            elif choice == "15":
                print(f"Prompt saved to {app.save_prompt()}")
            else:
                print("Unknown choice.")
        except (PromptMakerError, ValueError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            return 130


def add_global_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--proma-dir",
        type=Path,
        default=default_proma_dir(),
        help="Proma data directory (default: ~/Desktop/Proma or PROMA_DIR)",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prompt Maker by PNF7 — command-line edition",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    add_global_arguments(parser)
    subparsers = parser.add_subparsers(dest="command")

    interactive_parser = subparsers.add_parser("interactive", help="Open the interactive menu")
    interactive_parser.set_defaults(command="interactive")

    analyze_parser = subparsers.add_parser("analyze", help="Show the most frequent story words")
    analyze_parser.add_argument("story_file", nargs="?", type=Path)
    analyze_parser.add_argument("--top", type=int, default=10)

    generate_parser = subparsers.add_parser("generate", help="Build and append a prompt to the log")
    generate_parser.add_argument("--story-file", type=Path)
    generate_parser.add_argument("--sector", default="")
    generate_parser.add_argument("--guardrail")
    generate_parser.add_argument("--topic1", default="")
    generate_parser.add_argument("--topic2", default="")
    generate_parser.add_argument("--auto-top-two", action="store_true")
    generate_parser.add_argument("--transform", action="append", default=[])
    generate_parser.add_argument(
        "--physical",
        action="store_true",
        help="Add topic1 -> topic2 and the default physical-process transform",
    )
    generate_parser.add_argument(
        "--seed",
        type=int,
        default=0,
        metavar="N",
        help="Add N random Sutton–Silver rules",
    )
    generate_parser.add_argument("--causal-plane", default="")
    generate_parser.add_argument("--abstraction", type=int, default=0)
    generate_parser.add_argument("--preview", action="store_true")
    generate_parser.add_argument("--no-save", action="store_true")

    blacklist_parser = subparsers.add_parser("blacklist", help="Manage ignored story words")
    blacklist_sub = blacklist_parser.add_subparsers(dest="blacklist_action", required=True)
    blacklist_sub.add_parser("list", help="List blacklist words")
    blacklist_add = blacklist_sub.add_parser("add", help="Add words")
    blacklist_add.add_argument("words", nargs="+")
    blacklist_remove = blacklist_sub.add_parser("remove", help="Remove words")
    blacklist_remove.add_argument("words", nargs="+")

    seed_parser = subparsers.add_parser("seed", help="Create random Sutton–Silver rules")
    seed_parser.add_argument("--count", type=int, default=1)
    seed_parser.add_argument("--no-add", action="store_true", help="Only print the rules")

    config_parser = subparsers.add_parser("config", help="Show loaded configuration")
    config_parser.set_defaults(command="config")

    return parser


def run_command(args: argparse.Namespace) -> int:
    app = PromptMaker(args.proma_dir)
    command = args.command or "interactive"

    if command == "interactive":
        return interactive(app)

    if command == "analyze":
        if args.story_file:
            app.load_story(args.story_file)
        print_top_words(app, max(1, args.top))
        return 0

    if command == "generate":
        if args.story_file:
            app.load_story(args.story_file)
        app.sector = args.sector
        app.guardrail_enabled = args.guardrail is not None
        app.guardrail = args.guardrail or ""
        app.goal_topic1 = args.topic1
        app.subject_topic2 = args.topic2
        app.transforms = list(args.transform)
        app.causal_plane = args.causal_plane
        app.abstraction_level = args.abstraction
        if args.auto_top_two:
            app.use_top_two()
        if args.physical:
            if not app.goal_topic1 or not app.subject_topic2:
                raise PromptMakerError(
                    "--physical requires topic1 and topic2; provide them or use --auto-top-two."
                )
            app.add_rule(app.goal_topic1, app.subject_topic2)
            app.add_transform(DEFAULT_PHYSICAL_TRANSFORM)
        if args.seed > 0:
            app.seed_sutton_silver(count=args.seed)
        prompt = app.build_prompt()
        if args.preview or args.no_save:
            print(prompt)
        if not args.no_save:
            print(f"Prompt saved to {app.save_prompt()}")
        return 0

    if command == "blacklist":
        if args.blacklist_action == "list":
            print("\n".join(sorted(app.blacklist)))
        elif args.blacklist_action == "add":
            added = app.add_blacklist(args.words)
            app.save_blacklist()
            print("Added: " + (", ".join(added) if added else "nothing"))
        elif args.blacklist_action == "remove":
            removed = app.remove_blacklist(args.words)
            app.save_blacklist()
            print("Removed: " + (", ".join(removed) if removed else "nothing"))
        return 0

    if command == "seed":
        rules = app.seed_sutton_silver(count=max(1, args.count), add=not args.no_add)
        print("\n".join(rules))
        return 0

    if command == "config":
        print(f"Config file: {app.config_path}")
        sections = (
            ("Topics", app.config.topics),
            ("Guardrails", app.config.guardrails),
            ("Transforms", app.config.transforms),
            ("Causal diagrams", app.config.causal_diagrams),
        )
        for heading, values in sections:
            print(f"\n{heading}:")
            print("\n".join(f"  - {value}" for value in values) or "  (none)")
        return 0

    raise PromptMakerError(f"Unknown command: {command}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return run_command(args)
    except PromptMakerError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
