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
