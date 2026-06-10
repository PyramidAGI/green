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
