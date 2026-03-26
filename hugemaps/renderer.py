"""Main map rendering engine.

Orchestrates the complete map rendering pipeline: features, roads, labels,
grid, and page chrome. Uses matplotlib for vector output.
"""

import click
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.collections import LineCollection, PatchCollection
from matplotlib.figure import Figure
from matplotlib.patches import Polygon as MplPolygon
from shapely.geometry import (
    LineString,
    MultiLineString,
    MultiPolygon,
    Polygon,
)

from hugemaps.grid import draw_grid
from hugemaps.labels import LabelPlacer
from hugemaps.layout import (
    create_figure,
    draw_attribution,
    draw_legend,
    draw_scale_bar,
    draw_title,
)
from hugemaps.style import ROAD_PRIORITY, Style


def _geom_to_line_coords(geom) -> list[list[tuple[float, float]]]:
    """Extract line coordinate arrays from a geometry."""
    if isinstance(geom, LineString):
        return [list(geom.coords)]
    elif isinstance(geom, MultiLineString):
        return [list(line.coords) for line in geom.geoms]
    return []


def _geom_to_polygon_patches(geom) -> list[MplPolygon]:
    """Extract matplotlib polygon patches from a geometry."""
    patches = []
    if isinstance(geom, Polygon):
        if not geom.is_empty:
            patches.append(MplPolygon(
                np.array(geom.exterior.coords),
                closed=True,
            ))
    elif isinstance(geom, MultiPolygon):
        for poly in geom.geoms:
            if not poly.is_empty:
                patches.append(MplPolygon(
                    np.array(poly.exterior.coords),
                    closed=True,
                ))
    return patches


def render_water(ax: Axes, water_gdf: gpd.GeoDataFrame, style: Style) -> None:
    """Render water features (lakes, rivers, coastline)."""
    if water_gdf.empty:
        return

    click.echo("  Rendering water features...")
    patches = []
    lines = []

    for _, row in water_gdf.iterrows():
        geom = row.geometry
        p = _geom_to_polygon_patches(geom)
        if p:
            patches.extend(p)
        else:
            l = _geom_to_line_coords(geom)
            if l:
                lines.extend(l)

    if patches:
        pc = PatchCollection(
            patches,
            facecolor=style.water_color,
            edgecolor=style.water_edge_color,
            linewidth=0.8,
            alpha=style.water_alpha,
            zorder=1,
        )
        ax.add_collection(pc)

    if lines:
        lc = LineCollection(
            lines,
            colors=style.water_color,
            linewidths=1.5,
            alpha=style.water_alpha,
            zorder=1,
        )
        ax.add_collection(lc)


def render_parks(ax: Axes, parks_gdf: gpd.GeoDataFrame, style: Style) -> None:
    """Render parks and green spaces."""
    if parks_gdf.empty:
        return

    click.echo("  Rendering parks...")
    patches = []

    for _, row in parks_gdf.iterrows():
        p = _geom_to_polygon_patches(row.geometry)
        patches.extend(p)

    if patches:
        pc = PatchCollection(
            patches,
            facecolor=style.park_color,
            edgecolor=style.park_edge_color,
            linewidth=0.8,
            alpha=style.park_alpha,
            zorder=1,
        )
        ax.add_collection(pc)


def render_buildings(ax: Axes, buildings_gdf: gpd.GeoDataFrame, style: Style) -> None:
    """Render building footprints."""
    if buildings_gdf.empty:
        return

    click.echo(f"  Rendering {len(buildings_gdf):,} buildings...")
    patches = []

    for _, row in buildings_gdf.iterrows():
        p = _geom_to_polygon_patches(row.geometry)
        patches.extend(p)

    if patches:
        pc = PatchCollection(
            patches,
            facecolor=style.building_color,
            edgecolor=style.building_edge_color,
            linewidth=0.1,
            alpha=style.building_alpha,
            zorder=2,
        )
        ax.add_collection(pc)


def render_railways(ax: Axes, railways_gdf: gpd.GeoDataFrame, style: Style) -> None:
    """Render railway lines with dashed styling."""
    if railways_gdf.empty:
        return

    click.echo("  Rendering railways...")
    lines = []

    for _, row in railways_gdf.iterrows():
        l = _geom_to_line_coords(row.geometry)
        lines.extend(l)

    if lines:
        lc = LineCollection(
            lines,
            colors=style.railway_color,
            linewidths=style.railway_width,
            linestyles="dashed",
            zorder=3,
        )
        ax.add_collection(lc)


def render_roads(ax: Axes, streets_gdf: gpd.GeoDataFrame, style: Style) -> None:
    """Render roads with casing technique (outline + fill).

    Renders from lowest to highest priority, casings first then fills,
    to create the layered road appearance of Thomas Bros maps.
    """
    if streets_gdf.empty:
        return

    click.echo(f"  Rendering {len(streets_gdf):,} road segments...")

    # Group roads by class
    road_groups: dict[str, list] = {}
    for _, row in streets_gdf.iterrows():
        rc = row.get("road_class", "service")
        if rc not in road_groups:
            road_groups[rc] = []
        coords = _geom_to_line_coords(row.geometry)
        road_groups[rc].extend(coords)

    # Render order: lowest priority first (reversed ROAD_PRIORITY)
    render_order = list(reversed(ROAD_PRIORITY))
    # Add any classes not in ROAD_PRIORITY
    for rc in road_groups:
        if rc not in render_order:
            render_order.insert(0, rc)

    # Pass 1: Casings (outlines)
    for rc in render_order:
        if rc not in road_groups:
            continue
        lines = road_groups[rc]
        if not lines:
            continue

        rs = style.get_road_style(rc)
        if rs.casing_color is None:
            continue

        lc = LineCollection(
            lines,
            colors=rs.casing_color,
            linewidths=rs.casing_width,
            capstyle="round",
            joinstyle="round",
            zorder=rs.zorder_casing,
        )
        ax.add_collection(lc)

    # Pass 2: Fills
    for rc in render_order:
        if rc not in road_groups:
            continue
        lines = road_groups[rc]
        if not lines:
            continue

        rs = style.get_road_style(rc)

        lc = LineCollection(
            lines,
            colors=rs.fill_color,
            linewidths=rs.fill_width,
            capstyle="round",
            joinstyle="round",
            zorder=rs.zorder_fill,
        )
        ax.add_collection(lc)


def render_boundary(ax: Axes, boundary_gdf: gpd.GeoDataFrame, style: Style) -> None:
    """Render the city boundary as a subtle dashed line."""
    if boundary_gdf.empty:
        return

    for _, row in boundary_gdf.iterrows():
        geom = row.geometry
        patches = _geom_to_polygon_patches(geom)
        for patch in patches:
            patch.set_facecolor("none")
            patch.set_edgecolor(style.boundary_color)
            patch.set_linewidth(1.0)
            patch.set_linestyle("--")
            patch.set_alpha(0.5)
            patch.set_zorder(35)
            ax.add_patch(patch)


def render_map(
    city_name: str,
    city_data: dict[str, gpd.GeoDataFrame],
    figure_size: tuple[float, float],
    bounds: tuple[float, float, float, float],
    scale: float,
    style: Style,
    dpi: int = 300,
    grid_cols: int = 8,
    grid_rows: int = 10,
) -> Figure:
    """Render the complete map.

    Args:
        city_name: Name of the city for the title
        city_data: Dict of GeoDataFrames (streets, buildings, parks, etc)
        figure_size: (width_inches, height_inches) for the map area
        bounds: (minx, miny, maxx, maxy) in projected coordinates
        scale: meters per inch
        style: Style configuration
        dpi: Resolution for the figure
        grid_cols: Number of grid columns
        grid_rows: Number of grid rows

    Returns:
        matplotlib Figure ready for export
    """
    click.echo(f"\n{'='*60}")
    click.echo("  Rendering map")
    click.echo(f"{'='*60}\n")

    width_in, height_in = figure_size
    minx, miny, maxx, maxy = bounds

    # Create figure and axes
    fig, map_ax = create_figure(width_in, height_in, dpi=dpi)

    # Set map extent
    map_ax.set_xlim(minx, maxx)
    map_ax.set_ylim(miny, maxy)
    map_ax.set_facecolor(style.background)
    map_ax.set_xticks([])
    map_ax.set_yticks([])

    # Bold border around map area
    for spine in map_ax.spines.values():
        spine.set_edgecolor("#2C3E50")
        spine.set_linewidth(2.0)

    # Render layers back-to-front
    render_water(map_ax, city_data.get("water", gpd.GeoDataFrame()), style)
    render_parks(map_ax, city_data.get("parks", gpd.GeoDataFrame()), style)
    render_buildings(map_ax, city_data.get("buildings", gpd.GeoDataFrame()), style)
    render_railways(map_ax, city_data.get("railways", gpd.GeoDataFrame()), style)
    render_roads(map_ax, city_data.get("streets", gpd.GeoDataFrame()), style)
    render_boundary(map_ax, city_data.get("boundary", gpd.GeoDataFrame()), style)

    # Labels
    label_placer = LabelPlacer(style)
    label_placer.place_neighborhood_labels(
        map_ax, city_data.get("neighborhoods", gpd.GeoDataFrame()), scale
    )
    label_placer.place_street_labels(
        map_ax, city_data.get("streets", gpd.GeoDataFrame()), scale
    )

    # Grid reference
    draw_grid(map_ax, bounds, style, cols=grid_cols, rows=grid_rows)

    # Page chrome
    draw_title(fig, city_name, style)
    draw_legend(fig, style)
    draw_scale_bar(fig, scale, style)
    draw_attribution(fig, style)

    click.echo("\n  Map rendering complete!")
    return fig
