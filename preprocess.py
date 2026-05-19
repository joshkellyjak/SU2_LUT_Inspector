#!/usr/bin/env python3
"""Parse LUT_H2.drg and write per-level JSON files for the web viewer."""

import json
import os
import sys

DRG_FILE = "LUT_H2.drg"
OUTPUT_DIR = "data"


def parse_header(f):
    """Read header and return metadata dict. File cursor left at start of <Data>."""
    meta = {}
    line = f.readline()  # "Dragon library"
    while True:
        line = f.readline()
        if not line:
            break
        line = line.strip()

        if line == "[Version]":
            meta["version"] = f.readline().strip()

        elif line == "[Progress variable definition]":
            meta["progress_variable_def"] = f.readline().strip()

        elif line == "[Number of table levels]":
            meta["n_levels"] = int(f.readline().strip())

        elif line == "[Table levels]":
            levels = []
            for _ in range(meta["n_levels"]):
                levels.append(float(f.readline().strip()))
            meta["levels"] = levels

        elif line == "[Number of points]":
            pts = []
            for _ in range(meta["n_levels"]):
                pts.append(int(f.readline().strip()))
            meta["n_points"] = pts

        elif line == "[Number of triangles]":
            tri = []
            for _ in range(meta["n_levels"]):
                tri.append(int(f.readline().strip()))
            meta["n_triangles"] = tri

        elif line == "[Number of hull points]":
            hull = []
            for _ in range(meta.get("n_levels", 0)):
                hull.append(int(f.readline().strip()))
            meta["n_hull_points"] = hull

        elif line == "[Number of variables]":
            meta["n_vars"] = int(f.readline().strip())

        elif line == "[Variable names]":
            var_names = []
            for _ in range(meta["n_vars"]):
                entry = f.readline().strip()
                # format "1:Name"
                var_names.append(entry.split(":", 1)[1])
            meta["var_names"] = var_names

        elif line == "</Header>":
            break

    return meta


def parse_levels(f, meta, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    n_levels = meta["n_levels"]
    var_names = meta["var_names"]
    n_vars = meta["n_vars"]
    levels = meta["levels"]

    level_idx = -1
    current_cols = None  # list of lists, one per variable

    for raw_line in f:
        line = raw_line.strip()
        if not line:
            continue

        if line == "<Data>":
            continue

        if line == "</Data>":
            break

        if line == "<Level>":
            level_idx += 1
            current_cols = [[] for _ in range(n_vars)]
            pct = (level_idx + 1) / n_levels * 100
            print(f"\r  Processing level {level_idx + 1}/{n_levels} ({pct:.0f}%)...", end="", flush=True)
            continue

        if line == "</Level>":
            # Write this level's data
            data = {var_names[i]: current_cols[i] for i in range(n_vars)}
            out = {
                "level_index": level_idx,
                "mixture_fraction": levels[level_idx],
                "n_points": len(current_cols[0]),
                "data": data,
            }
            fname = os.path.join(output_dir, f"level_{level_idx:02d}.json")
            with open(fname, "w") as out_f:
                json.dump(out, out_f, separators=(",", ":"))
            current_cols = None
            continue

        # Data row: tab-separated floats
        if current_cols is not None:
            vals = line.split("\t")
            if len(vals) == n_vars:
                for i, v in enumerate(vals):
                    current_cols[i].append(float(v))

    print()  # newline after progress


def main():
    if not os.path.exists(DRG_FILE):
        print(f"Error: {DRG_FILE} not found in current directory.")
        sys.exit(1)

    print(f"Parsing {DRG_FILE} ...")
    with open(DRG_FILE, "r") as f:
        meta = parse_header(f)

    print(f"  Found {meta['n_levels']} levels, {meta['n_vars']} variables")
    print(f"  Variables: {', '.join(meta['var_names'])}")

    # Write metadata
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    meta_out = {
        "version": meta["version"],
        "progress_variable_def": meta["progress_variable_def"],
        "n_levels": meta["n_levels"],
        "levels": meta["levels"],
        "n_points": meta["n_points"],
        "n_vars": meta["n_vars"],
        "var_names": meta["var_names"],
    }
    with open(os.path.join(OUTPUT_DIR, "metadata.json"), "w") as f:
        json.dump(meta_out, f, indent=2)
    print(f"  Wrote {OUTPUT_DIR}/metadata.json")

    print("Parsing level data...")
    with open(DRG_FILE, "r") as f:
        # Skip to <Data>
        for line in f:
            if line.strip() == "<Data>":
                # Put <Data> back by parsing levels from here
                # Actually we already consumed the line; parse_levels handles <Data> check
                # Re-open and seek is cleaner
                break
        # Re-open to parse data section cleanly
    with open(DRG_FILE, "r") as f:
        parse_header(f)  # skip header again
        parse_levels(f, meta, OUTPUT_DIR)

    print(f"Done. Data written to '{OUTPUT_DIR}/' directory.")
    print(f"\nNext step: run 'python serve.py' and open http://localhost:8080")


if __name__ == "__main__":
    main()
