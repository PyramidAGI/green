import os

SIXD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sixd")
OUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "overview.txt")

query = input("Search string: ").strip()

matches = [f for f in os.listdir(SIXD_DIR) if query in f and os.path.isfile(os.path.join(SIXD_DIR, f))]

if not matches:
    print(f"No files found matching '{query}' in {SIXD_DIR}")
else:
    with open(OUT_FILE, "w", encoding="utf-8") as out:
        for filename in sorted(matches):
            path = os.path.join(SIXD_DIR, filename)
            with open(path, encoding="utf-8") as f:
                content = f.read().strip()
            if content:
                out.write(content + "\n")
    print(f"Written {len(matches)} file(s) to overview.txt: {', '.join(sorted(matches))}")
