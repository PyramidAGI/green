import csv

ENTITY_HEADERS = ["qaci", "summary", "thing1", "thing2", "property", "v", "threshold", "message"]
SENTENCE_MAX = 15


def read_blocks(path):
    blocks = []
    current = {"sentence": None, "rows": []}

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";")
        for raw in reader:
            cols = [c.strip() for c in raw]
            while cols and cols[-1] == "":
                cols.pop()

            if not cols:
                if current["sentence"] or current["rows"]:
                    blocks.append(current)
                    current = {"sentence": None, "rows": []}
                continue

            # col0 has sentence + col1 has entity data on same line
            if cols[0] and len(cols) >= 2 and cols[1]:
                current["sentence"] = cols[0]
                row_data = cols[1:]
            # entity row only (col0 empty)
            elif not cols[0] and len(cols) >= 2 and cols[1]:
                row_data = cols[1:]
            # standalone sentence line
            else:
                current["sentence"] = cols[0]
                continue

            row = dict(zip(ENTITY_HEADERS, row_data + [""] * len(ENTITY_HEADERS)))
            current["rows"].append(row)

    if current["sentence"] or current["rows"]:
        blocks.append(current)

    return blocks


def print_table(rows, sentence):
    col_widths = {h: len(h) for h in ENTITY_HEADERS}
    col_widths["sentence"] = SENTENCE_MAX + 2

    for row in rows:
        for h in ENTITY_HEADERS:
            col_widths[h] = max(col_widths[h], len(row.get(h, "")))

    all_headers = ["sentence"] + ENTITY_HEADERS
    header_line = "  ".join(h.ljust(col_widths[h]) for h in all_headers)
    sep = "  ".join("-" * col_widths[h] for h in all_headers)
    print(f"  {header_line}")
    print(f"  {sep}")

    sent_short = ((sentence or "")[:SENTENCE_MAX] + "..") if sentence else ""
    for i, row in enumerate(rows):
        sent_col = (sent_short if i == 0 else "").ljust(col_widths["sentence"])
        data_cols = "  ".join(row.get(h, "").ljust(col_widths[h]) for h in ENTITY_HEADERS)
        print(f"  {sent_col}  {data_cols}")


def print_grounding(path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";")
        headers = [c.strip() for c in next(reader)]
        rows = [[c.strip() for c in row] for row in reader if any(c.strip() for c in row)]

    col_widths = [max(len(headers[i]), max((len(r[i]) for r in rows if i < len(r)), default=0))
                  for i in range(len(headers))]

    header_line = "  ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    sep = "  ".join("-" * w for w in col_widths)
    print(f"  {header_line}")
    print(f"  {sep}")
    for row in rows:
        print("  " + "  ".join((row[i] if i < len(row) else "").ljust(col_widths[i]) for i in range(len(headers))))


def main():
    print("=== grounding.csv ===")
    print_grounding("grounding.csv")

    print("\n=== log.csv ===")
    blocks = read_blocks("log.csv")
    for i, block in enumerate(blocks):
        print(f"\n[Block {i + 1}]")
        if block["rows"]:
            print_table(block["rows"], block["sentence"])


if __name__ == "__main__":
    main()
