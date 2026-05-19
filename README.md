# Flamelet LUT Viewer

An (AI slop) interactive browser-based tool for inspecting hydrogen flamelet lookup tables in the SU2 `.drg` format. Supports scatter plotting of any table variable, a 3D scatter view, and a visualisation of the trapezoidal map (slab decomposition) that SU2 builds internally for table lookup.

I made this with Claude so if it doesn't work blame him!

![Trapezoidal map view showing the triangle mesh, slab boundaries, and hull vertices for a single mixture fraction level](docs/trapmap_preview.png)

---

## Requirements

- Python 3.7+
- A modern browser (Chrome / Firefox / Safari / Edge)
- No additional Python packages — only the standard library is used.

---

## Setup

### 1. Place your `.drg` file

Put your flamelet table (e.g. `LUT_H2.drg`) in the same directory as the scripts. The preprocessors expect to find the file in the working directory.

### 2. Preprocess the point data

```bash
python preprocess.py
```

Reads the `<Data>` section of the `.drg` file and writes one JSON file per mixture fraction level to `data/level_NN.json`, plus a `data/metadata.json` index. For a 50-level, ~5 000 pt/level table this takes roughly 30–60 s and produces ~95 MB of JSON.

### 3. Preprocess the mesh data

```bash
python preprocess_mesh.py
```

Reads the `<Connectivity>` (triangle indices) and `<Hull>` (convex hull point indices) sections and writes `data/mesh_NN.json` for each level. Required for the **Trapezoidal Map** view.

### 4. Start the local server

```bash
python serve.py
```

Starts a simple HTTP server on `http://localhost:8080`. Keep this terminal open while using the viewer.

### 5. Open the viewer

Navigate to **http://localhost:8080** in your browser.

---

## Data directory layout

```
TableViz/
├── LUT_H2.drg            # source flamelet table (Dragon / SU2 format)
├── preprocess.py         # step 1: extract point data → data/level_NN.json
├── preprocess_mesh.py    # step 2: extract mesh data  → data/mesh_NN.json
├── serve.py              # local HTTP server
├── index.html            # viewer application
└── data/
    ├── metadata.json     # variable names, level values, point counts
    ├── level_00.json     # point data for level 0 (all 21 variables)
    ├── mesh_00.json      # triangle connectivity + hull indices for level 0
    ├── ...
    ├── level_49.json
    └── mesh_49.json
```

Level data files are loaded lazily as you navigate between levels, and adjacent levels are pre-fetched in the background, so switching feels near-instant after the first visit.

---

## Using the viewer

### Level navigation

All three views share the same **Mixture Fraction Level** panel in the sidebar.

| Control | Action |
|---------|--------|
| Slider | Jump to any of the 50 mixture fraction levels |
| Prev / Next buttons | Step one level at a time |
| ← → arrow keys | Step one level at a time (keyboard shortcut) |

The current mixture fraction value Z is shown below the slider.

---

### Scatter view

A 2D scatter plot of any two table variables.

- **X axis / Y axis** — choose from all 21 variables. Defaults to Progress Variable vs Total Enthalpy.
- **Color variable** — map any variable to a continuous colorscale. Choose from 8 colorscales.
- **Overlay all levels** — draws cached levels as faint background points for context.
- **Marker size** — adjusts point size.

---

### 3D Scatter view

Same as the Scatter view but with an independent **Z axis** selector, rendered as an interactive 3D scatter plot.

- Rotate by dragging, zoom with the scroll wheel.
- The camera angle **persists** when you change levels or update the color variable — it only resets when you change one of the three axis variables.
- **Overlay all levels** renders cached levels as semi-transparent background clouds.

---

### Trapezoidal Map view

Visualises the slab decomposition that SU2's `CTrapezoidalMap` builds at runtime (see `CTrapezoidalMap.cpp`). The coordinate space is (Progress Variable, Total Enthalpy) for the selected mixture fraction level.

The slab method partitions the domain into vertical bands at each unique Progress Variable sample value. Within each band, triangle edges are sorted by their Y intercept at the band midpoint, enabling O(log n) point location.

| Element | Description |
|---------|-------------|
| Colored points | Sample points for the current level, colored by the chosen variable |
| Grey mesh | Delaunay triangle edges (toggle on/off) |
| Blue dashed lines | Slab grid — every Nth band boundary (adjust with density slider) |
| Red shaded region | Currently selected slab |
| Red tick marks | Triangle edges that intersect the selected slab, shown at their Y intercept at the band midpoint — these are the values stored in `y_edge_at_band_mid` |
| Orange open circles | Convex hull vertices (toggle on/off) |

**Slab band index slider** — selects which band to highlight. The info panel below it reports the band's PV range and how many edges intersect it.

**Slab grid density** — show every Nth boundary line. The domain typically has ~5 000 unique PV values per level; set this to 100–500 to see well-separated lines.

---

## Table format

The `.drg` (Dragon library) format used by SU2 contains:

- **Header** — version, progress variable definition, per-level point/triangle/hull counts, variable names.
- **`<Data>`** — one `<Level>` block per mixture fraction level; each row is a tab-separated list of variable values for one sample point.
- **`<Connectivity>`** — one `<Level>` block per level; each row is three whitespace-separated zero-based point indices forming a triangle.
- **`<Hull>`** — one `<Level>` block per level; each row is the index of one convex hull vertex.

The 21 variables in `LUT_H2.drg` are:

| # | Name |
|---|------|
| 1 | ProgressVariable |
| 2 | EnthalpyTot |
| 3 | MixtureFraction |
| 4 | Temperature |
| 5 | MolarWeightMix |
| 6 | DiffusionCoefficient |
| 7 | Conductivity |
| 8 | ViscosityDyn |
| 9 | Cp |
| 10 | Beta_ProgVar |
| 11 | Beta_Enth_Thermal |
| 12 | Beta_Enth |
| 13 | Beta_MixFrac |
| 14 | ProdRateTot_PV |
| 15 | Y_dot_pos-H2O |
| 16 | Y_dot_neg-H2O |
| 17 | Y_dot_net-H2O |
| 18 | Y-H2O |
| 19 | Heat_Release |
| 20 | Density |
| 21 | FlameletID |
