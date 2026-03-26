# HugeMaps

Generate large, printable wall-sized city maps from OpenStreetMap data — styled after the iconic **Thomas Bros / Thomas Guide** maps from the 2000s.

Give it a city name. It downloads the data, calculates the right size, renders every street with a label, and outputs print-ready PDF and SVG files.

```
hugemaps "San Francisco, California"
```

## Features

- **Automatic OSM data download** — streets, buildings, parks, water, railways, neighborhoods
- **Thomas Bros styling** — tan background, bold white road corridors with casings, orange freeways, yellow arterials, color-coded road hierarchy
- **100% label coverage** — every named road gets at least one label, guaranteed
- **Adaptive sizing** — figure scales up automatically until all labels fit; no file size limits
- **Vector output** — PDF (300 DPI, embedded fonts) and SVG (resolution-independent)
- **Wall-sized** — outputs can be 36×48 inches, 60×80 inches, or larger
- **Grid reference system** — A–H × 1–10 grid overlay with margin labels
- **Local caching** — downloaded OSM data cached as GeoPackage files for fast re-runs
- **Casing road rendering** — two-pass technique (outline + fill) creates bordered road corridors

## The Thomas Bros Style

Thomas Bros maps were the definitive street atlases of Southern California from the 1950s through the 2000s. HugeMaps recreates their distinctive look:

| Element | Color | Description |
|---------|-------|-------------|
| Background | `#DDD0B0` | Distinctly tan/khaki paper |
| Freeways | `#E87020` fill, `#6B3310` casing | Bold orange bands with dark brown outlines |
| Trunk roads | `#F0C020` fill, `#8B6914` casing | Bright yellow with gold outlines |
| Primary roads | `#FFFFFF` fill, `#666666` casing | Wide white corridors with dark gray outlines |
| Secondary roads | `#FFFFFF` fill, `#777777` casing | White corridors with gray outlines |
| Residential | `#FFFFFF` fill, `#777777` casing | Visible white bands — the signature street grid |
| Parks | `#B5D98C` | Rich green with defined edges |
| Water | `#8DC8E8` | Clear blue |
| Buildings | `#D5CCBA` | Subtle warm gray footprints |
| Railways | `#555555` | Dashed lines |

The key to the Thomas Bros look: **every road type gets a visible casing (outline)**, creating unmistakable white corridors against the tan background. Even residential streets are bold white bands, not thin lines.

## Installation

Requires Python 3.10+.

```bash
git clone https://github.com/elcamino/hugemaps.git
cd hugemaps
pip install -e .
```

### Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| [osmnx](https://osmnx.readthedocs.io/) | >=2.0.0 | OSM data download via Overpass API |
| [geopandas](https://geopandas.org/) | >=1.0.0 | Geospatial DataFrames |
| [shapely](https://shapely.readthedocs.io/) | >=2.0 | Geometry operations |
| [matplotlib](https://matplotlib.org/) | >=3.8 | Vector rendering engine (PDF/SVG) |
| [numpy](https://numpy.org/) | any | Numerical operations |
| [click](https://click.palletsprojects.com/) | >=8.0 | CLI framework |
| [rtree](https://rtree.readthedocs.io/) | >=1.0 | Spatial indexing for label collision |
| [pyproj](https://pyproj4.github.io/pyproj/) | >=3.0 | CRS projection/reprojection |

## Quick Start

```bash
# Generate a map of Beverly Hills (auto-sized, both PDF and SVG)
hugemaps "Beverly Hills, California"

# Specify minimum size and PDF only
hugemaps "Manhattan, New York" --size 36x48 --format pdf

# Skip buildings for faster rendering, SVG only
hugemaps "London, UK" --no-buildings --format svg

# Custom output directory and grid dimensions
hugemaps "Paris, France" --output ./maps/ --grid-cols 10 --grid-rows 12

# Force re-download (ignore cache)
hugemaps "Tokyo, Japan" --no-cache --dpi 200
```

## CLI Reference

```
Usage: hugemaps [OPTIONS] CITY
```

| Option | Default | Description |
|--------|---------|-------------|
| `CITY` | *(required)* | Geocodable place name (e.g., `"San Francisco, California"`) |
| `-s, --size WxH` | auto | Minimum paper size in inches (e.g., `36x48`). Auto-calculated if omitted. |
| `-f, --format` | `both` | Output format: `pdf`, `svg`, or `both` |
| `-o, --output PATH` | `.` | Output directory |
| `--dpi N` | `300` | DPI for PDF output |
| `--no-buildings` | off | Skip building footprints (significantly faster) |
| `--no-cache` | off | Force re-download of all OSM data |
| `--grid-cols N` | `8` | Number of grid reference columns (A–H) |
| `--grid-rows N` | `10` | Number of grid reference rows (1–10) |
| `--max-size N` | `160` | Maximum dimension in inches |
| `--version` | | Show version and exit |

Output files are named `{CityName}_map.pdf` and `{CityName}_map.svg` in the output directory.

## How It Works

HugeMaps runs a six-stage pipeline:

### 1. Download

Uses [osmnx](https://osmnx.readthedocs.io/) to geocode the city name via Nominatim, then downloads features from the Overpass API:

| Layer | OSM Tags |
|-------|----------|
| Streets | `highway=*` |
| Buildings | `building=*` |
| Parks | `leisure=[park,garden,golf_course,nature_reserve]`, `landuse=[grass,forest,recreation_ground,meadow,village_green]` |
| Water | `natural=[water,bay,coastline]`, `waterway=*` |
| Railways | `railway=[rail,light_rail,subway,tram]` |
| Neighborhoods | `place=[suburb,neighbourhood,quarter,village,hamlet]` |

All data is cached locally as GeoPackage files (see [Caching](#caching)).

### 2. Project

Reprojects all features from WGS84 (EPSG:4326) to the appropriate UTM zone for accurate meter-based measurements. The UTM zone is auto-detected from the city's centroid.

### 3. Classify

Roads are classified into 15 types based on their `highway` tag (see [Road Style Reference](#road-style-reference)). Features with multiple tags are resolved by priority.

### 4. Size

The [adaptive sizing algorithm](#adaptive-sizing) computes the optimal figure dimensions so that every named road can fit a label. The aspect ratio always matches the city's geographic bounding box.

### 5. Render

Layers are rendered back-to-front using matplotlib:

1. **Background** — tan fill
2. **Water** — polygons and lines
3. **Parks** — green polygons
4. **Buildings** — gray footprints
5. **Railways** — dashed lines
6. **Roads** — two-pass casing technique (outlines first, then fills)
7. **City boundary** — dashed outline
8. **Neighborhood labels** — large bold uppercase text
9. **Street labels** — rotated along roads with white halo
10. **Grid** — reference lines and margin labels
11. **Title, legend, scale bar, attribution**

### 6. Export

The matplotlib figure is saved as vector PDF (with embedded Type 42 fonts) and/or SVG (with text elements, not paths). Both formats are resolution-independent and can be printed at any size.

## Architecture

```
hugemaps/
├── __init__.py      # Version string
├── __main__.py      # python -m hugemaps support
├── cli.py           # Click CLI entry point and pipeline orchestration
├── data.py          # OSM data download and GeoPackage caching
├── geometry.py      # UTM projection, road classification, adaptive sizing
├── style.py         # Thomas Bros color palette, road widths, font config
├── renderer.py      # Matplotlib rendering engine, layer orchestration
├── labels.py        # R-tree label placement with 100% coverage guarantee
├── grid.py          # A-H × 1-10 grid reference overlay
├── layout.py        # Title block, legend, scale bar, attribution
└── export.py        # PDF/SVG export with font embedding
```

| Module | Key Components |
|--------|---------------|
| `cli.py` | `main()` — full pipeline from city name to output files |
| `data.py` | `download_all()` — orchestrates 7 feature downloads with caching |
| `geometry.py` | `compute_optimal_size()` — iterative sizing algorithm |
| `style.py` | `Style` dataclass — all visual parameters; `RoadStyle` — per-road-type config |
| `renderer.py` | `render_map()` — orchestrates all rendering; `render_roads()` — casing technique |
| `labels.py` | `LabelPlacer` class — R-tree collision detection, two-phase placement |
| `grid.py` | `draw_grid()` — grid lines and margin labels |
| `layout.py` | `create_figure()`, `draw_title()`, `draw_legend()`, `draw_scale_bar()` |
| `export.py` | `export_pdf()`, `export_svg()` — vector output with font handling |

## Label Placement

HugeMaps guarantees **every named road gets at least one label**. This is achieved through a two-phase algorithm using an R-tree spatial index for collision detection.

### Phase 1: Guaranteed Placement

1. Group all road segments by name
2. Sort by priority (freeways first, service roads last)
3. For each unique named road:
   - Try 7 positions along the longest segment: 50%, 35%, 65%, 25%, 75%, 15%, 85%
   - Check each position against the R-tree for collisions
   - If no collision-free position found, try shorter segments of the same road
4. **Force-placement fallback** — if all positions collide:
   - Shrink font to 85%, 70%, 55% of normal
   - Try perpendicular offsets (±1.5×, ±3.0× font height)
   - Last resort: place at 50% of longest segment at 50% font size

Result: 100% of named roads are labeled.

### Phase 2: Density Fill

For roads longer than 2,000 meters, repeat labels are added at regular intervals (up to 5 per road) so the name appears in multiple grid cells. These are best-effort — skipped if they would collide.

### Label Rendering

- Street labels are rotated to match the road direction
- Text is kept readable (never upside-down — angles are normalized to ±90°)
- White halo effect (4pt stroke) ensures readability against both white roads and tan background
- Neighborhood labels are horizontal, bold, uppercase, with expanded font stretch

## Adaptive Sizing

The figure size is not fixed. HugeMaps scales the output until all labels fit:

1. Count unique named roads and estimate total label area needed
2. Start with a base size (36 inches on the shorter dimension, or user-specified `--size`)
3. Iteratively increase by 15% until label area is < 40% of map area
4. Aspect ratio always matches the city's geographic bounding box
5. Cap at `--max-size` (default: 160 inches / ~13 feet)

For a dense city like Manhattan with thousands of named streets, the output might be 60×80 inches. For a small suburb, 30×24 inches. File size is explicitly not a concern.

## Caching

Downloaded OSM data is cached locally to avoid redundant API calls:

```
~/.hugemaps/cache/
└── Beverly_Hills_California_a1b2c3d4e5f6/
    ├── boundary.gpkg
    ├── streets.gpkg
    ├── buildings.gpkg
    ├── parks.gpkg
    ├── water.gpkg
    ├── railways.gpkg
    ├── neighborhoods.gpkg
    └── metadata.json
```

- Format: GeoPackage (`.gpkg`) — handles mixed geometry types
- Cache key: sanitized city name + SHA-256 hash
- To force re-download: use `--no-cache`
- To clear all cache: `rm -rf ~/.hugemaps/cache/`

## Output Formats

### PDF

- Vector format with embedded Type 42 (TrueType) fonts
- Default 300 DPI (configurable with `--dpi`)
- Print-ready — send directly to a large-format printer
- Fonts remain sharp at any zoom level
- `bbox_inches="tight"` with 0.2-inch padding

### SVG

- Resolution-independent vector graphics
- Text rendered as SVG `<text>` elements (not paths) — searchable and editable
- Can be opened in Inkscape, Illustrator, or any web browser
- Ideal for further editing or web display

## Road Style Reference

All 15 road classifications with their visual parameters:

| Road Type | Fill | Casing | Fill Width | Casing Width | Label Size | Bold |
|-----------|------|--------|-----------|--------------|-----------|------|
| Motorway | `#E87020` | `#6B3310` | 8.0 pt | 11.0 pt | 14.0 pt | Yes |
| Motorway link | `#E87020` | `#6B3310` | 5.0 pt | 7.0 pt | 10.0 pt | Yes |
| Trunk | `#F0C020` | `#8B6914` | 7.0 pt | 9.5 pt | 13.0 pt | Yes |
| Trunk link | `#F0C020` | `#8B6914` | 4.0 pt | 5.5 pt | 10.0 pt | Yes |
| Primary | `#FFFFFF` | `#666666` | 9.0 pt | 12.0 pt | 12.0 pt | Yes |
| Primary link | `#FFFFFF` | `#666666` | 6.0 pt | 8.0 pt | 10.0 pt | Yes |
| Secondary | `#FFFFFF` | `#777777` | 8.0 pt | 11.0 pt | 11.0 pt | Yes |
| Secondary link | `#FFFFFF` | `#777777` | 5.0 pt | 7.0 pt | 9.0 pt | No |
| Tertiary | `#FFFFFF` | `#777777` | 7.0 pt | 10.0 pt | 10.0 pt | No |
| Tertiary link | `#FFFFFF` | `#777777` | 5.0 pt | 7.0 pt | 9.0 pt | No |
| Residential | `#FFFFFF` | `#777777` | 7.0 pt | 10.0 pt | 9.5 pt | No |
| Living street | `#FFFFFF` | `#777777` | 6.0 pt | 8.5 pt | 9.0 pt | No |
| Unclassified | `#FFFFFF` | `#777777` | 6.0 pt | 8.5 pt | 9.0 pt | No |
| Service | `#F0E8D5` | `#888888` | 3.5 pt | 5.0 pt | 8.0 pt | No |
| Pedestrian | `#F0E8D5` | `#888888` | 4.0 pt | 5.5 pt | 8.5 pt | No |

Roads are rendered using a **casing technique**: first all outlines (casings) are drawn, then all fills on top. This creates the bordered corridor effect where road edges are always visible.

## Customization

The `Style` dataclass in `hugemaps/style.py` controls all visual parameters. To customize:

```python
from hugemaps.style import Style

# All defaults can be overridden
custom_style = Style(
    background="#F0F0F0",          # lighter background
    neighborhood_font_size=28.0,   # larger neighborhood labels
    grid_line_alpha=0.2,           # more subtle grid
    title_font_size=42.0,          # bigger title
)
```

Key parameters you might want to adjust:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `background` | `#DDD0B0` | Map background color |
| `neighborhood_font_size` | `22.0` | Neighborhood label size (pt) |
| `neighborhood_font_alpha` | `0.55` | Neighborhood label transparency |
| `grid_line_alpha` | `0.35` | Grid line transparency |
| `grid_label_size` | `14.0` | Grid margin label size (pt) |
| `title_font_size` | `36.0` | Title text size (pt) |
| `label_halo_width` | `4.0` | White outline around labels (pt) |
| `building_alpha` | `0.6` | Building footprint transparency |
| `park_alpha` | `0.85` | Park fill transparency |
| `water_alpha` | `0.9` | Water fill transparency |

Individual road styles can be modified by replacing entries in the `road_styles` dict.

## Page Layout

The output page is composed of:

```
┌──────────────────────────────────────────┐
│              CITY NAME                   │  ← Dark navy title banner
│           City, State/Country            │
├──A────B────C────D────E────F────G────H──┤
│1                                       1│
│                                         │
│2          [Map Content]                2│  ← Map area with grid overlay
│           roads, parks, water,          │
│3          buildings, labels             3│
│                                         │
│...                                   ...│
│                                         │
│10                                     10│
├──A────B────C────D────E────F────G────H──┤
│ LEGEND                    SCALE         │  ← Legend box + scale bar
│ [road samples] [swatches] ████░░░░ 1km  │
│        © OpenStreetMap contributors     │  ← Attribution
└──────────────────────────────────────────┘
```

Margins: 1.5" top (title), 1.8" bottom (legend/attribution), 1.0" sides (grid labels).

## Performance Notes

- **Small cities** (e.g., Beverly Hills): ~1–2 minutes for download, ~30 seconds to render
- **Large cities** (e.g., Los Angeles): ~5–10 minutes for download, ~2–5 minutes to render
- **Buildings** are the slowest layer — use `--no-buildings` for faster iteration
- **Caching** makes subsequent runs much faster (seconds instead of minutes)
- **Memory**: large cities may require 4–8 GB RAM for rendering

## Attribution

Maps generated by HugeMaps include the required attribution:

> Map data &copy; OpenStreetMap contributors

This attribution is automatically rendered at the bottom of every map. [OpenStreetMap data](https://www.openstreetmap.org/copyright) is available under the Open Database License (ODbL).

## License

MIT
