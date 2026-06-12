#!/usr/bin/env python3
"""The five wires of triangle_wires.svg, as a runnable CLI.

Three measure wires (in) and two influence wires (out), against a
simulated environment:

  1. sun    -> radiation   measure lux
  2. plant  -> stat        measure soil moisture
  3. people -> val         query: ask a human (the q sensor)
  4. drive  -> motor       influence: set motor speed
  5. reward -> people      query: thank a human (the q actuator)

The cluster file five_wires_cluster.csv holds the same five wires as
records (see sixd/recordexplain.csv); the [c] command executes it row
by row. Every measurement and influence is appended to wirelog.csv in
the same record format.

Commands: 1-5, a=all five, c=run cluster file, s=state, q=quit
"""

import datetime
import math
import random
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
CLUSTER_CSV = SCRIPT_DIR / "five_wires_cluster.csv"
WIRELOG_CSV = SCRIPT_DIR / "wirelog.csv"
FIELDS = 9


class Environment:
    """Simulated world: a sun, a plant, people, and a motor."""

    def __init__(self) -> None:
        self.moisture = 70.0      # percent
        self.mood = 6.0           # people mood 0-10
        self.motor_speed = 0.0    # percent of max
        self.steps = 0

    def tick(self) -> None:
        self.steps += 1
        self.moisture = max(0.0, self.moisture - random.uniform(0.5, 2.0))
        self.mood = max(0.0, self.mood - 0.1)
        self.motor_speed *= 0.95  # spins down without new commands

    def lux(self) -> int:
        hour = datetime.datetime.now().hour + datetime.datetime.now().minute / 60
        daylight = max(0.0, math.sin((hour - 6) / 12 * math.pi))
        return int(daylight * 50000 + random.uniform(0, 2000))


def log_record(label: str, kind: str, verb: str, obj: str, value: str) -> None:
    fields = [label, kind, verb, obj, value, "", "", "", ""]
    with WIRELOG_CSV.open("a", encoding="utf-8") as f:
        f.write(";".join(fields[:FIELDS]) + "\n")


def measure_sun(env: Environment) -> None:
    value = env.lux()
    print(f"  [wire 1] sun -> radiation: {value} lux")
    log_record("measure the sun", "c", "measure", "sun", str(value))


def measure_plant(env: Environment) -> None:
    value = round(env.moisture, 1)
    print(f"  [wire 2] plant -> stat: {value}% soil moisture")
    log_record("measure the plant", "c", "measure", "plant", str(value))


def query_people(env: Environment) -> None:
    raw = input("  [wire 3] q: how do the people feel today (0-10)? ").strip()
    try:
        env.mood = max(0.0, min(10.0, float(raw.replace(",", "."))))
    except ValueError:
        print(f"  not a number, keeping previous reading {env.mood:.1f}")
    print(f"  people -> val: {env.mood:.1f}/10")
    log_record("ask the people", "q", "measure", "people", f"{env.mood:.1f}")


def drive_motor(env: Environment, target: str = "") -> None:
    if not target:
        target = input("  [wire 4] motor speed 0-100? ").strip()
    try:
        env.motor_speed = max(0.0, min(100.0, float(target)))
    except ValueError:
        print("  not a number, motor unchanged")
        return
    print(f"  drive -> motor: set to {env.motor_speed:.0f}%")
    log_record("drive the motor", "c", "influence", "motor", f"{env.motor_speed:.0f}")


def thank_people(env: Environment) -> None:
    print("  [wire 5] q: a thank-you goes out to the people")
    env.mood = min(10.0, env.mood + 1.0)
    print(f"  reward -> people: mood rises to {env.mood:.1f}/10")
    log_record("thank the people", "q", "influence", "people", f"{env.mood:.1f}")


def show_state(env: Environment) -> None:
    print(f"  steps: {env.steps}   lux: {env.lux()}   moisture: {env.moisture:.1f}%"
          f"   mood: {env.mood:.1f}/10   motor: {env.motor_speed:.0f}%")


def run_cluster(env: Environment) -> None:
    if not CLUSTER_CSV.exists():
        print(f"  cluster file not found: {CLUSTER_CSV.name}")
        return
    print(f"  running {CLUSTER_CSV.name}")
    for line in CLUSTER_CSV.read_text(encoding="utf-8").splitlines():
        parts = line.split(";")
        if len(parts) < 7 or not parts[2]:
            continue  # separator or malformed row
        label, verb, obj, value = parts[0], parts[2], parts[3], parts[6]
        print(f"  -- {label}")
        if verb == "measure" and obj == "sun":
            measure_sun(env)
        elif verb == "measure" and obj == "plant":
            measure_plant(env)
        elif verb == "measure" and obj == "people":
            query_people(env)
        elif verb == "influence" and obj == "motor":
            drive_motor(env, value)
        elif verb == "influence" and obj == "people":
            thank_people(env)
        else:
            print(f"  unknown wire: {verb} {obj}")
        env.tick()


def main() -> None:
    env = Environment()
    print("Five wires — measure and influence")
    print("1=sun 2=plant 3=people 4=motor 5=thanks  a=all  c=cluster  s=state  q=quit")

    while True:
        try:
            choice = input("\n> ").strip().casefold()
        except (EOFError, KeyboardInterrupt):
            print()
            return

        if choice == "q":
            return
        if choice == "1":
            measure_sun(env)
        elif choice == "2":
            measure_plant(env)
        elif choice == "3":
            query_people(env)
        elif choice == "4":
            drive_motor(env)
        elif choice == "5":
            thank_people(env)
        elif choice == "a":
            measure_sun(env)
            measure_plant(env)
            query_people(env)
            drive_motor(env)
            thank_people(env)
        elif choice == "c":
            run_cluster(env)
            continue
        elif choice == "s":
            show_state(env)
        else:
            print("  use 1-5, a, c, s, or q")
            continue
        env.tick()


if __name__ == "__main__":
    main()
