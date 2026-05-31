import csv
from pathlib import Path

# CONST = 1 to use log1.csv, CONST = 0 (or any falsy value) keeps log.csv
CONST = 0

def get_log_file() -> Path:
    # A function rather than a module-level constant so that external scripts can override CONST after import
    # and have the new value take effect. A constant is evaluated once at import time and won't update.
    import template_program
    return Path(__file__).parent / (f"log{template_program.CONST}.csv" if template_program.CONST else "log.csv")
EXAMPLE_FILE = Path(__file__).parent / "examplecluster.txt"

FIELDS = ["natural language input", "e0", "e1", "e2", "e3", "e4", "v", "threshold", "message output"]


def load_example_cluster() -> tuple[str, list[str]]:
    # Loads a cluster from examplecluster.txt: one sentence with multiple matches.
    # The natural language sentence is on the first line only; subsequent lines start with ';'.
    # Returns the sentence and a list of match strings (fields e0-e4, v, threshold, message output).
    lines = [l for l in EXAMPLE_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]
    sentence = lines[0].split(";")[0]
    matches = [";".join(l.split(";")[1:]) for l in lines]
    return sentence, matches


def parse_match(match: str) -> dict:
    parts = match.split(";")
    keys = ["e0", "e1", "e2", "e3", "e4", "v", "threshold", "message output"]
    return {k: (parts[i] if i < len(parts) else "") for i, k in enumerate(keys)}


def log(sentence: str, matches: list[str]) -> None:
    append_matches_cluster(get_log_file(), sentence, matches)


def append_matches_cluster(path: Path, sentence: str, matches: list[str]) -> None:
    rows_to_write = []
    for index, match in enumerate(matches):
        parsed = parse_match(match)
        row = {
            "natural language input": sentence if index == 0 else "",
            "e0": parsed.get("e0", ""),
            "e1": parsed.get("e1", ""),
            "e2": parsed.get("e2", ""),
            "e3": parsed.get("e3", ""),
            "e4": parsed.get("e4", ""),
            "v": parsed.get("v", ""),
            "threshold": parsed.get("threshold", ""),
            "message output": "",
        }
        if any(value for key, value in row.items() if key != "natural language input") or row["natural language input"]:
            rows_to_write.append(row)

    if not rows_to_write:
        return

    with path.open("a", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle, delimiter=";")
        writer.writerow(["", "", "", "", "", "", "", "", ""])
        for row in rows_to_write:
            writer.writerow(
                [
                    row["natural language input"],
                    row["e0"],
                    row["e1"],
                    row["e2"],
                    row["e3"],
                    row["e4"],
                    row["v"],
                    row["threshold"],
                    row["message output"],
                ]
            )
        writer.writerow(["", "", "", "", "", "", "", "", ""])


def count_clusters() -> int:
    if not get_log_file().exists():
        return 0
    count = 0
    in_cluster = False
    with get_log_file().open(encoding="utf-8-sig", newline="") as f:
        for row in csv.reader(f, delimiter=";"):
            if any(cell.strip() for cell in row):
                if not in_cluster:
                    count += 1
                    in_cluster = True
            else:
                in_cluster = False
    return count


def get_cluster(cluster_number: int) -> list[list[str]]:
    if not get_log_file().exists():
        return []
    clusters = []
    current = []
    with get_log_file().open(encoding="utf-8-sig", newline="") as f:
        for row in csv.reader(f, delimiter=";"):
            if any(cell.strip() for cell in row):
                current.append(row)
            elif current:
                clusters.append(current)
                current = []
    if current:
        clusters.append(current)
    if cluster_number == -1:  # -1 returns the most recently added cluster
        return clusters[-1] if clusters else []
    if cluster_number < 1 or cluster_number > len(clusters):
        return []
    return clusters[cluster_number - 1]


def recall(cluster_number: int) -> None:
    rows = get_cluster(cluster_number)
    if not rows:
        print("Cluster not found.")
        return
    sentence = rows[0][0]
    matches = [";".join(row[1:]) for row in rows]
    log(sentence, matches)

def solve_problem(cluster_number: int) -> list[list[str]]:
    # Get cluster, send to LLM, parse result into rows.
    # Pass -1 to solve the most recently added cluster.
    cluster = get_cluster(cluster_number)
    if not cluster:
        return []
    # TODO: call LLM with cluster and parse response into list of rows
    return []


def create_tree(cluster_number: int = -1) -> list[list[str]]:
    # Build a problem tree from the given cluster via LLM. Defaults to -1 (most recently added cluster).
    cluster = get_cluster(cluster_number)
    if not cluster:
        return []
    # TODO: parse response into list of rows
    import anthropic
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=1024,
        messages=[{"role": "user", "content": str(cluster)}],
    )
    _ = response.content[0].text
    return []


def check_log() -> None:
    if not get_log_file().exists():
        print("log.csv not found.")
        return
    errors = []
    with get_log_file().open(encoding="utf-8-sig", newline="") as f:
        for i, row in enumerate(csv.reader(f, delimiter=";"), start=1):
            if len(row) != 9:
                errors.append(f"  line {i}: expected 9 fields, got {len(row)} — {row}")
    if errors:
        print(f"Found {len(errors)} error(s) in log.csv:")
        for e in errors:
            print(e)
    else:
        print("log.csv OK — no formatting errors.")


def main():
    print("Press 'l' to log, 'c' to check, 'count' to count, 'g' to get, 'recall' to recall, 's' to solve, 't' to create tree, 'q' to quit.")
    while True:
        key = input("> ").strip().lower()
        if key == "l":
            sentence, matches = load_example_cluster()
            log(sentence, matches)
            print(f"Logged: {sentence}")
        elif key == "c":
            check_log()
        elif key == "count":
            print(f"Clusters in log.csv: {count_clusters()}")
        elif key == "g":
            n = input("Cluster number: ").strip()
            rows = get_cluster(int(n))
            if rows:
                for row in rows:
                    print(";".join(row))
            else:
                print("Cluster not found.")
        elif key == "recall":
            n = input("Cluster number to recall: ").strip()
            recall(int(n))
            print(f"Cluster {n} appended to log.")
        elif key == "s":
            n = input("Cluster number to solve: ").strip()
            result = solve_problem(int(n))
            if result:
                for row in result:
                    print(";".join(row))
            else:
                print("No result.")
        elif key == "t":
            n = input("Cluster number to create tree for: ").strip()
            result = create_tree(int(n))
            if result:
                for row in result:
                    print(";".join(row))
            else:
                print("No result.")
        elif key == "q":
            break


if __name__ == "__main__":
    main()
