# Green

## glasses.py

glasses.py can start three different programs. They are the culmination of a year's work on AI.

A pygame launcher shaped like a pair of glasses.

The glasses image is displayed as the background. Three clickable file links are placed inside the lens areas:

- **six_dots.py** — left lens (top)
- **yellow.py** — left lens (bottom)
- **prompt_maker_cli.py** — right lens

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
