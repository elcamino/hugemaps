"""OSM data download and caching.

Downloads streets, buildings, parks, water, railways, and neighborhoods
for a given city using osmnx and the Overpass API. Caches results locally.
"""

import hashlib
import json
import logging
from pathlib import Path

import click
import geopandas as gpd
import osmnx as ox
from shapely.geometry import MultiPolygon, Polygon

logger = logging.getLogger(__name__)

CACHE_DIR = Path.home() / ".hugemaps" / "cache"


def _cache_key(city_name: str) -> str:
    """Generate a filesystem-safe cache key from the city name."""
    h = hashlib.sha256(city_name.lower().strip().encode()).hexdigest()[:16]
    safe = "".join(c if c.isalnum() or c in "-_ " else "" for c in city_name)
    safe = safe.strip().replace(" ", "_")[:60]
    return f"{safe}_{h}"


def _cache_path(city_name: str) -> Path:
    return CACHE_DIR / _cache_key(city_name)


def _get_boundary_polygon(boundary_gdf: gpd.GeoDataFrame) -> Polygon | MultiPolygon:
    """Extract the polygon geometry from a boundary GeoDataFrame."""
    geom = boundary_gdf.union_all()
    if isinstance(geom, (Polygon, MultiPolygon)):
        return geom
    raise ValueError(f"Boundary geometry is not a polygon: {type(geom)}")


def get_city_boundary(city_name: str, use_cache: bool = True) -> gpd.GeoDataFrame:
    """Download or load cached city boundary polygon."""
    cache = _cache_path(city_name)
    cache_file = cache / "boundary.gpkg"

    if use_cache and cache_file.exists():
        click.echo(f"  Loading cached boundary for '{city_name}'...")
        return gpd.read_file(cache_file)

    click.echo(f"  Geocoding '{city_name}'...")
    gdf = ox.geocode_to_gdf(city_name)

    cache.mkdir(parents=True, exist_ok=True)
    gdf.to_file(cache_file, driver="GPKG")
    return gdf


def _download_features(
    boundary_gdf: gpd.GeoDataFrame,
    tags: dict,
    label: str,
    cache_file: Path,
    use_cache: bool = True,
) -> gpd.GeoDataFrame:
    """Download OSM features within the boundary polygon."""
    if use_cache and cache_file.exists():
        click.echo(f"  Loading cached {label}...")
        return gpd.read_file(cache_file)

    click.echo(f"  Downloading {label}...")
    polygon = _get_boundary_polygon(boundary_gdf)

    try:
        gdf = ox.features_from_polygon(polygon, tags=tags)
        # Keep only relevant geometry types
        gdf = gdf[gdf.geometry.notnull()].copy()
        # Save cache
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        # GeoPackage handles mixed geometry types better than GeoJSON
        gdf.to_file(cache_file, driver="GPKG")
        click.echo(f"    Found {len(gdf)} {label} features")
        return gdf
    except Exception as e:
        click.echo(f"    Warning: Could not download {label}: {e}")
        return gpd.GeoDataFrame()


def download_streets(
    boundary_gdf: gpd.GeoDataFrame, city_name: str, use_cache: bool = True
) -> gpd.GeoDataFrame:
    """Download street/road network features."""
    cache = _cache_path(city_name) / "streets.gpkg"
    return _download_features(
        boundary_gdf,
        tags={"highway": True},
        label="streets",
        cache_file=cache,
        use_cache=use_cache,
    )


def download_buildings(
    boundary_gdf: gpd.GeoDataFrame, city_name: str, use_cache: bool = True
) -> gpd.GeoDataFrame:
    """Download building footprints."""
    cache = _cache_path(city_name) / "buildings.gpkg"
    return _download_features(
        boundary_gdf,
        tags={"building": True},
        label="buildings",
        cache_file=cache,
        use_cache=use_cache,
    )


def download_parks(
    boundary_gdf: gpd.GeoDataFrame, city_name: str, use_cache: bool = True
) -> gpd.GeoDataFrame:
    """Download parks and green spaces."""
    cache = _cache_path(city_name) / "parks.gpkg"
    return _download_features(
        boundary_gdf,
        tags={
            "leisure": ["park", "garden", "golf_course", "nature_reserve"],
            "landuse": [
                "grass",
                "forest",
                "recreation_ground",
                "meadow",
                "village_green",
            ],
        },
        label="parks",
        cache_file=cache,
        use_cache=use_cache,
    )


def download_water(
    boundary_gdf: gpd.GeoDataFrame, city_name: str, use_cache: bool = True
) -> gpd.GeoDataFrame:
    """Download water features (lakes, rivers, etc)."""
    cache = _cache_path(city_name) / "water.gpkg"
    return _download_features(
        boundary_gdf,
        tags={"natural": ["water", "bay", "coastline"], "waterway": True},
        label="water",
        cache_file=cache,
        use_cache=use_cache,
    )


def download_railways(
    boundary_gdf: gpd.GeoDataFrame, city_name: str, use_cache: bool = True
) -> gpd.GeoDataFrame:
    """Download railway lines."""
    cache = _cache_path(city_name) / "railways.gpkg"
    return _download_features(
        boundary_gdf,
        tags={"railway": ["rail", "light_rail", "subway", "tram"]},
        label="railways",
        cache_file=cache,
        use_cache=use_cache,
    )


def download_neighborhoods(
    boundary_gdf: gpd.GeoDataFrame, city_name: str, use_cache: bool = True
) -> gpd.GeoDataFrame:
    """Download neighborhood/suburb place labels."""
    cache = _cache_path(city_name) / "neighborhoods.gpkg"
    return _download_features(
        boundary_gdf,
        tags={"place": ["suburb", "neighbourhood", "quarter", "village", "hamlet"]},
        label="neighborhoods",
        cache_file=cache,
        use_cache=use_cache,
    )


def download_all(
    city_name: str,
    use_cache: bool = True,
    include_buildings: bool = True,
) -> dict[str, gpd.GeoDataFrame]:
    """Download all map data for a city.

    Returns a dict with keys: boundary, streets, buildings, parks, water,
    railways, neighborhoods.
    """
    click.echo(f"\n{'='*60}")
    click.echo(f"  Downloading map data for: {city_name}")
    click.echo(f"{'='*60}\n")

    boundary = get_city_boundary(city_name, use_cache=use_cache)

    data = {"boundary": boundary}

    data["streets"] = download_streets(boundary, city_name, use_cache)
    data["parks"] = download_parks(boundary, city_name, use_cache)
    data["water"] = download_water(boundary, city_name, use_cache)
    data["railways"] = download_railways(boundary, city_name, use_cache)
    data["neighborhoods"] = download_neighborhoods(boundary, city_name, use_cache)

    if include_buildings:
        data["buildings"] = download_buildings(boundary, city_name, use_cache)
    else:
        data["buildings"] = gpd.GeoDataFrame()
        click.echo("  Skipping buildings (--no-buildings)")

    # Save metadata
    meta_path = _cache_path(city_name) / "metadata.json"
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta = {
        "city_name": city_name,
        "features": {k: len(v) for k, v in data.items()},
    }
    meta_path.write_text(json.dumps(meta, indent=2))

    total = sum(len(v) for v in data.values())
    click.echo(f"\n  Total features downloaded: {total:,}")
    return data
