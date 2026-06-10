# Green

## six_dots.py

A navigation/inspection dashboard for a self-organizing problem-solving system. The goal: turn a problem tree into causal diagrams and double triangles.

The six dots are the system's components:

1. **Orchestrator** — the coordinator; knows which causal diagram connects to which double triangle.
2. **Causal diagram** — holds factors and criteria (the *analysis* of a problem: what causes what).
3. **Double triangle** — an executable unit: a sensor, an actuator, control/nav/plan, and transforms (built with `load_double_triangle.py`). Essentially a small control loop that can act on the world.
4. **Bus** — picks up compressed sentences from the orchestrator and distributes information between components.
5. **Log** — the shared record (the log.csv record format the CSVs use).
6. **Do** — holds 9 functions that map onto `template_program.py`; the part that actually executes.

The intended pipeline: gather a *cluster* of problems → convert the cluster into a *problem tree* → convert the tree into *causal diagrams* (understanding) and *double triangles* (action) → "make it so". The same structure works for both technical and organizational problems — the actuator can be a motor or a person/team.

Controls: arrow keys select a component, digits 1–9 pick a numbered instance (e.g. `doubletriangle3`), Enter loads its CSV from `sixd/`, and `q` opens a form that takes a problem-tree file as input for the conversion.

A browser version is available in `six_dots.html`. Serve it locally (`python -m http.server`) and open http://localhost:8000/six_dots.html.

### Run

```
python six_dots.py
```

## glasses.py

glasses.py can start two different programs. They are the culmination of a year's work on AI.

A pygame launcher shaped like a pair of glasses.

The glasses image is displayed as the background. Two clickable file links are placed inside the lens areas:

- **six_dots.py** — left lens
- **load_double_triangle.py** — right lens

Clicking a link launches it with Python. Links highlight in red on hover.

### Requirements

- Python 3
- pygame (`pip install pygame`)

### Run

```
python glasses.py
```

## load_double_triangle.py

A CLI tool for building a double triangle CSV file (`sixd/doubletriangle1.csv`) in the log.csv record format.

Enter transforms one by one. Type `l` to save, `q` to quit.

Each transform is written as a row with `c` in e0, `transform` in e1, the left side in e2, and the right side in e3. Five fixed rows are always appended: `sensor`, `actuator`, `control`, `plan`, and `nav`.

Input shorthand: `lux power` is treated as `lux -> power`.

Quarks from `numbered quarks.csv` can be referenced by number: `k` lists all quarks, `k N M` adds a transform from quark N to quark M (e.g. `k 1 5` adds `container -> radiation`).

### Run

```
python load_double_triangle.py
```

## From double triangle to Raspberry Pi program

A double triangle CSV (e.g. `sixd/doubletriangle1.csv`: lux→power, force→speed) can become a running Raspberry Pi program without writing program logic by hand. The CSV is not data, it's a wiring diagram: each row tells a generic runtime what to connect, and the quark names are the plugs.

1. **A driver catalog maps quark names to hardware.** One small Python library on the Pi where every quark name that can appear in a transform has a driver: `lux` → BH1750 light sensor on I2C, `force` → force-sensitive resistor on an MCP3008 ADC, `power` → PWM duty cycle on a GPIO pin, `speed` → motor driver (L298N). Written once, reused by every double triangle.

2. **Each `transform` row becomes one wire.** `c;transform;lux;power` reads as: "the lux reading continuously drives the power output." A bright room dims an LED. `force;speed` means: squeeze the FSR harder, motor spins faster. Every transform starts as the same normalized linear map (input range → output range), only the endpoints differ.

3. **The five fixed rows are the skeleton of the program, not features.**
   - `sensor` → the read phase of the loop (poll all left-side quarks)
   - `actuator` → the write phase (push all right-side quarks)
   - `control` → the loop itself, say 10 Hz, optionally with a setpoint/PID per wire
   - `plan` → a sequence of setpoints over time ("dim to 20% after 22:00")
   - `nav` → a tiny state machine that switches between plans (day mode / night mode)

4. **The program is then ~50 lines and never changes.** It parses `doubletriangleN.csv`, looks up each quark in the driver catalog, builds the wire list, and runs the control loop. Want different behavior? Don't edit Python — build a new double triangle with `load_double_triangle.py` and point the Pi at it. The `q` in the sensor row could even mean "this triangle queries its sensor remotely," letting one Pi sense and another actuate over the bus.

5. **The orchestrator closes the loop.** Since six_dots knows which causal diagram connects to which double triangle, a problem tree like "plant dries out" → causal diagram → `soil_moisture -> water_pump` transform → the Pi greenhouse waters itself. That's the "make it so" path, ending in actual GPIO pulses.

The punchline: the Pi runs one permanent interpreter, and the double triangle CSVs become the *programs* — swappable behavior files a non-programmer can author by picking quark numbers.

## A causal diagram for a non-technical application

A causal diagram holds factors and criteria (see `sixd/dotexplain.csv`). Example: **a volunteer-retention dashboard for a local club** (sports club, choir, scouting group — any organization that bleeds volunteers).

The mapping:

- **Factors** are the causes people quit, taken straight from a problem tree: "feels unappreciated", "tasks unclear", "meetings too long", "conflict with board", "no say in decisions". The quark list already speaks this language — `group`, `conflict`, `own`, `reward`, `val`, `organization`, `dominate` are organizational quarks, not technical ones.

- **Criteria** are the measurable thresholds that make the soft stuff hard: "fewer than 2 thank-yous per month", "more than 3 hours of meetings per week", "0 decisions influenced this quarter". Each factor row gets a criterion row next to it. That's the entire trick: the causal diagram forces vague complaints into checkable statements.

- **The double triangle then runs the social control loop.** Sensor = a 3-question monthly survey (or just counting who shows up). Actuator = a person: the board member who must act when a criterion trips. Transforms like `conflict -> group` ("when conflict rises, schedule a group session") or `activity -> reward` ("logged hours trigger a thank-you"). Control = the monthly board meeting, plan = the season program, nav = switching between "recruiting mode" and "retention mode".

The point this demonstrates: the same six-dots pipeline — problem tree → causal diagram → double triangle — works when the sensor is a survey instead of a lux meter and the actuator is a chairperson instead of a PWM pin. One generic tool for technical *and* organizational problems.

## A double triangle for a non-technical application

`sixd/doubletriangle6.csv` holds five transforms: `effort -> location`, `tool -> compress`, `transaction -> reward`, `energy -> organization`, `activity -> organization`. Read organizationally, this is **a community repair café** — a monthly event where volunteers fix visitors' broken items.

The five wires:

- **`effort -> location`** — route volunteer effort to where the queue is. If the bicycle station is backed up and the electronics table is idle, effort moves there. Where you put effort *is* a location decision.

- **`tool -> compress`** — the right tool compresses the job. A soldering station turns a 40-minute fiddle into a 5-minute fix. Investing in tools is investing in shorter queues.

- **`transaction -> reward`** — every completed repair (the transaction) triggers a visible reward: the donation jar, a photo of the fixed item on the wall, the visitor's thank-you. No repair goes unrewarded, or volunteers stop coming.

- **`energy -> organization`** — schedule the organizing work (rosters, inventory, cleanup) when team energy is high, right after a successful event — not when everyone is drained.

- **`activity -> organization`** — let recurring activity crystallize into structure. When the same person ends up at the sewing table three events in a row, that becomes a named role. Structure follows activity, not the other way around.

And the fixed skeleton: **sensor** = the sign-in sheet and queue length per station, **actuator** = the day coordinator who moves people and opens stations, **control** = the shift lead walking rounds every half hour, **plan** = the event calendar for the season, **nav** = switching between "intake mode" (morning rush) and "repair mode" (afternoon focus).

Same CSV format that drives a Raspberry Pi greenhouse — but here the control loop runs on coffee and goodwill.
