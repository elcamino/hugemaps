"""CLI entry point for HugeMaps.

Usage:
    hugemaps "San Francisco, California" --format pdf,svg --output ./output/
"""

from pathlib import Path

import click
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend

from hugemaps import __version__
from hugemaps.data import download_all
from hugemaps.export import export_pdf, export_svg
from hugemaps.geometry import (
    calculate_bounds,
    calculate_extent_meters,
    classify_roads,
    compute_optimal_size,
    estimate_utm_crs,
    filter_renderable_streets,
    project_to_meters,
)
from hugemaps.renderer import render_map
from hugemaps.style import Style


def _parse_size(ctx, param, value):
    """Parse a WxH size string into (width, height) tuple."""
    if value is None:
        return None
    try:
        parts = value.lower().split("x")
        return (float(parts[0]), float(parts[1]))
    except (ValueError, IndexError):
        raise click.BadParameter(f"Size must be WxH format (e.g., 36x48), got: {value}")


@click.command()
@click.argument("city")
@click.option(
    "--size", "-s",
    default=None,
    callback=_parse_size,
    help="Minimum paper size in inches WxH (e.g., 36x48). Default: auto-calculated.",
)
@click.option(
    "--format", "-f", "output_format",
    default="both",
    type=click.Choice(["pdf", "svg", "both"], case_sensitive=False),
    help="Output format (default: both).",
)
@click.option(
    "--output", "-o",
    default=".",
    type=click.Path(),
    help="Output directory (default: current directory).",
)
@click.option("--dpi", default=300, type=int, help="DPI for PDF output (default: 300).")
@click.option("--no-buildings", is_flag=True, help="Skip building footprints (faster).")
@click.option("--no-cache", is_flag=True, help="Force re-download of OSM data.")
@click.option("--grid-cols", default=8, type=int, help="Grid reference columns (default: 8).")
@click.option("--grid-rows", default=10, type=int, help="Grid reference rows (default: 10).")
@click.option(
    "--max-size",
    default=160.0,
    type=float,
    help="Maximum dimension in inches (default: 160).",
)
@click.version_option(version=__version__)
def main(
    city: str,
    size: tuple[float, float] | None,
    output_format: str,
    output: str,
    dpi: int,
    no_buildings: bool,
    no_cache: bool,
    grid_cols: int,
    grid_rows: int,
    max_size: float,
):
    """Generate a large printable wall map of CITY in the Thomas Bros style.

    CITY should be a geocodable place name like "San Francisco, California"
    or "Paris, France".

    Examples:

        hugemaps "Beverly Hills, California"

        hugemaps "Manhattan, New York" --size 36x48 --format pdf

        hugemaps "London, UK" --no-buildings --format svg
    """
    click.echo(f"\n  HugeMaps v{__version__}")
    click.echo(f"  {'='*50}")

    style = Style()

    # Step 1: Download data
    city_data = download_all(
        city,
        use_cache=not no_cache,
        include_buildings=not no_buildings,
    )

    # Step 2: Project everything to meters (UTM)
    click.echo("\n  Projecting to metric CRS...")
    target_crs = estimate_utm_crs(city_data["boundary"])

    projected_data = {}
    for key, gdf in city_data.items():
        if not gdf.empty:
            projected_data[key] = project_to_meters(gdf, target_crs)
        else:
            projected_data[key] = gdf

    # Step 3: Classify roads
    click.echo("  Classifying roads...")
    if not projected_data.get("streets", None) is None and not projected_data["streets"].empty:
        projected_data["streets"] = classify_roads(projected_data["streets"])
        projected_data["streets"] = filter_renderable_streets(projected_data["streets"])

    # Step 4: Calculate bounds and optimal size
    bounds = calculate_bounds(projected_data["boundary"])
    width_m, height_m = calculate_extent_meters(bounds)
    click.echo(f"  City extent: {width_m/1000:.1f} x {height_m/1000:.1f} km")

    figure_size = compute_optimal_size(
        bounds,
        projected_data.get("streets", None) or __import__("geopandas").GeoDataFrame(),
        style,
        min_size_in=size,
        max_dimension_in=max_size,
    )

    width_in, height_in = figure_size
    scale = max(width_m / width_in, height_m / height_in)  # meters per inch

    # Step 5: Render
    fig = render_map(
        city_name=city,
        city_data=projected_data,
        figure_size=figure_size,
        bounds=bounds,
        scale=scale,
        style=style,
        dpi=dpi,
        grid_cols=grid_cols,
        grid_rows=grid_rows,
    )

    # Step 6: Export
    output_dir = Path(output)
    safe_name = "".join(c if c.isalnum() or c in "-_ " else "" for c in city)
    safe_name = safe_name.strip().replace(" ", "_")[:60]

    if output_format in ("pdf", "both"):
        pdf_path = output_dir / f"{safe_name}_map.pdf"
        export_pdf(fig, pdf_path, dpi=dpi)

    if output_format in ("svg", "both"):
        svg_path = output_dir / f"{safe_name}_map.svg"
        export_svg(fig, svg_path)

    # Cleanup
    matplotlib.pyplot.close(fig)

    click.echo(f"\n  {'='*50}")
    click.echo(f"  Done! Map files saved to: {output_dir.resolve()}")
    click.echo()


if __name__ == "__main__":
    main()
