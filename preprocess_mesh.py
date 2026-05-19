#!/usr/bin/env python3
"""Parse <Connectivity> and <Hull> sections from LUT_H2.drg, write data/mesh_NN.json."""

import json
import os
import sys

DRG_FILE = "LUT_H2.drg"
DATA_DIR = "data"


def parse_section(f, n_levels, n_items_per_level, parse_row):
    """Generic level-section parser. parse_row converts a stripped line to data."""
    level_idx = -1
    current = None
    results = []

    for raw_line in f:
        line = raw_line.strip()
        if not line:
            continue
        if line in ("<Connectivity>", "<Hull>", "</Connectivity>", "</Hull>", "<Data>"):
            continue
        if line == "<Level>":
            level_idx += 1
            current = []
            pct = (level_idx + 1) / n_levels * 100
            print(f"\r  {level_idx + 1}/{n_levels} ({pct:.0f}%)...", end="", flush=True)
            continue
        if line == "</Level>":
            results.append(current)
            current = None
            if level_idx + 1 >= n_levels:
                break
            continue
        if current is not None:
            current.append(parse_row(line))

    print()
    return results


def main():
    if not os.path.exists(DRG_FILE):
        print(f"Error: {DRG_FILE} not found.")
        sys.exit(1)

    if not os.path.exists(os.path.join(DATA_DIR, "metadata.json")):
        print("Error: data/metadata.json not found. Run preprocess.py first.")
        sys.exit(1)

    with open(os.path.join(DATA_DIR, "metadata.json")) as f:
        meta = json.load(f)

    n_levels = meta["n_levels"]

    # Fast-forward to <Connectivity>
    print("Scanning to <Connectivity> section...")
    conn_data = None
    hull_data = None

    with open(DRG_FILE, "r") as f:
        for raw_line in f:
            if raw_line.strip() == "<Connectivity>":
                break

        print("Parsing triangle connectivity...")

        def parse_tri(line):
            parts = line.split("\t")
            return [int(parts[0]), int(parts[1]), int(parts[2])]

        conn_data = parse_section(f, n_levels, meta["n_triangles"], parse_tri)

        # Now fast-forward to <Hull>
        for raw_line in f:
            if raw_line.strip() == "<Hull>":
                break

        print("Parsing hull points...")

        def parse_hull(line):
            return int(line.strip())

        hull_data = parse_section(f, n_levels, meta["n_hull_points"], parse_hull)

    print("Writing mesh JSON files...")
    for idx in range(n_levels):
        out = {
            "level_index": idx,
            "mixture_fraction": meta["levels"][idx],
            "triangles": conn_data[idx],
            "hull": hull_data[idx],
        }
        fname = os.path.join(DATA_DIR, f"mesh_{idx:02d}.json")
        with open(fname, "w") as f:
            json.dump(out, f, separators=(",", ":"))
        pct = (idx + 1) / n_levels * 100
        print(f"\r  Written {idx + 1}/{n_levels} ({pct:.0f}%)...", end="", flush=True)

    print(f"\nDone. Mesh files written to '{DATA_DIR}/'.")


if __name__ == "__main__":
    main()
