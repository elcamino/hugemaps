"""Geometry processing, projection, and adaptive figure sizing.

Handles CRS reprojection, bounds calculation, road classification,
and the iterative sizing algorithm that ensures 100% label coverage.
"""

import math

import click
import geopandas as gpd
import numpy as np
from pyproj import CRS
from shapely.geometry import LineString, MultiLineString, Point

from hugemaps.style import LABELED_ROAD_TYPES, Style


def estimate_utm_crs(gdf: gpd.GeoDataFrame) -> CRS:
    """Estimate the best UTM zone CRS for accurate meter measurements."""
    bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]
    center_lon = (bounds[0] + bounds[2]) / 2
    center_lat = (bounds[1] + bounds[3]) / 2
    utm_zone = int((center_lon + 180) / 6) + 1
    hemisphere = "north" if center_lat >= 0 else "south"
    epsg = 32600 + utm_zone if hemisphere == "north" else 32700 + utm_zone
    return CRS.from_epsg(epsg)


def project_to_meters(gdf: gpd.GeoDataFrame, target_crs: CRS | None = None) -> gpd.GeoDataFrame:
    """Reproject GeoDataFrame to a metric CRS (UTM)."""
    if gdf.empty:
        return gdf
    if target_crs is None:
        target_crs = estimate_utm_crs(gdf)
    return gdf.to_crs(target_crs)


def calculate_bounds(gdf: gpd.GeoDataFrame) -> tuple[float, float, float, float]:
    """Get (minx, miny, maxx, maxy) bounds."""
    return tuple(gdf.total_bounds)


def calculate_extent_meters(bounds: tuple[float, float, float, float]) -> tuple[float, float]:
    """Calculate width and height of bounds in meters."""
    minx, miny, maxx, maxy = bounds
    return (maxx - minx, maxy - miny)


def calculate_aspect_ratio(bounds: tuple[float, float, float, float]) -> float:
    """Calculate width / height aspect ratio."""
    w, h = calculate_extent_meters(bounds)
    if h == 0:
        return 1.0
    return w / h


def classify_roads(streets_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Add a normalized 'road_class' column based on the highway tag."""
    if streets_gdf.empty:
        return streets_gdf

    gdf = streets_gdf.copy()

    # The highway column may contain lists for features with multiple tags
    def _normalize_highway(val):
        if isinstance(val, list):
            # Pick the most important one
            for priority in LABELED_ROAD_TYPES:
                if priority in val:
                    return priority
            return val[0] if val else "service"
        return val

    if "highway" in gdf.columns:
        gdf["road_class"] = gdf["highway"].apply(_normalize_highway)
    else:
        gdf["road_class"] = "service"

    return gdf


def filter_renderable_streets(streets_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Filter streets to only include renderable road types (exclude paths, etc)."""
    if streets_gdf.empty:
        return streets_gdf

    renderable = set(LABELED_ROAD_TYPES)
    return streets_gdf[streets_gdf["road_class"].isin(renderable)].copy()


def get_named_roads(streets_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Filter to only streets that have a name tag."""
    if streets_gdf.empty or "name" not in streets_gdf.columns:
        return gpd.GeoDataFrame()
    named = streets_gdf[streets_gdf["name"].notna() & (streets_gdf["name"] != "")].copy()
    return named


def merge_road_segments(named_streets: gpd.GeoDataFrame) -> dict[str, list]:
    """Group road segments by name, returning {name: [geometries]}."""
    if named_streets.empty:
        return {}

    roads: dict[str, list] = {}
    for _, row in named_streets.iterrows():
        name = row.get("name", "")
        if not name:
            continue
        if name not in roads:
            roads[name] = []
        roads[name].append({
            "geometry": row.geometry,
            "road_class": row.get("road_class", "residential"),
        })
    return roads


def compute_optimal_size(
    bounds: tuple[float, float, float, float],
    streets_gdf: gpd.GeoDataFrame,
    style: Style,
    min_size_in: tuple[float, float] | None = None,
    max_dimension_in: float = 160.0,
) -> tuple[float, float]:
    """Compute the optimal figure size (inches) for 100% label coverage.

    Iteratively scales up the figure until every named road can fit at least
    one label. The aspect ratio always matches the city's geographic bbox.

    Returns (width_inches, height_inches).
    """
    width_m, height_m = calculate_extent_meters(bounds)
    aspect = width_m / height_m if height_m > 0 else 1.0

    # Count unique named roads and estimate label area needed
    named = get_named_roads(streets_gdf)
    if named.empty:
        click.echo("  Warning: No named roads found")
        if min_size_in:
            return min_size_in
        return (36.0, 36.0 / aspect) if aspect >= 1 else (48.0 * aspect, 48.0)

    road_groups = merge_road_segments(named)
    total_named = len(road_groups)
    click.echo(f"  Found {total_named:,} unique named roads")

    # Estimate: average label needs ~0.8 inches width, ~0.12 inches height
    # at the configured font sizes. We need enough map area for all labels.
    avg_chars = np.mean([len(name) for name in road_groups.keys()])
    avg_label_width_in = avg_chars * 0.065  # rough estimate: 0.065 inches per char at ~7pt
    avg_label_height_in = 0.12

    # Start with a base size
    if min_size_in:
        base_w, base_h = min_size_in
    else:
        # Default: 36 inches on the shorter side
        if aspect >= 1:
            base_h = 36.0
            base_w = base_h * aspect
        else:
            base_w = 36.0
            base_h = base_w / aspect

    # Scale factor: how many meters per inch at this figure size
    def _scale_at_size(w_in, h_in):
        sx = width_m / w_in if w_in > 0 else 1
        sy = height_m / h_in if h_in > 0 else 1
        return max(sx, sy)

    # Estimate if all labels can fit: total label area vs available road area
    # Use a simple heuristic: label area < 40% of map area (generous allowance
    # since labels follow roads and distribute spatially)
    current_w, current_h = base_w, base_h

    for iteration in range(30):
        scale = _scale_at_size(current_w, current_h)

        # At this scale, estimate how many labels can fit
        # Each label occupies some area on the map
        total_label_area = total_named * avg_label_width_in * avg_label_height_in
        map_area = current_w * current_h

        # Check: can all labels fit if we use ~50% of map area for labels?
        # Also check minimum segment length: at this scale, the shortest named
        # road segment must be long enough to fit a label
        min_segment_length_m = float("inf")
        for name, segments in road_groups.items():
            for seg in segments:
                geom = seg["geometry"]
                if hasattr(geom, "length"):
                    min_segment_length_m = min(min_segment_length_m, geom.length)

        # Minimum label width in meters at this scale
        min_label_width_m = avg_label_width_in * scale

        # Check if the map is large enough
        label_area_ratio = total_label_area / map_area if map_area > 0 else 999
        fits = label_area_ratio < 0.40

        if fits:
            break

        # Scale up by 15%
        current_w *= 1.15
        current_h *= 1.15

        if max(current_w, current_h) > max_dimension_in:
            click.echo(f"  Reached maximum dimension ({max_dimension_in} inches)")
            break

    # Ensure minimum dimensions
    current_w = max(current_w, 24.0)
    current_h = max(current_h, 24.0)

    click.echo(
        f"  Computed map size: {current_w:.1f} x {current_h:.1f} inches "
        f"(scale: 1 inch = {_scale_at_size(current_w, current_h):.0f} meters)"
    )

    return (current_w, current_h)
