"""Street name and neighborhood label placement engine.

Guarantees every named road gets at least one label using R-tree spatial
indexing for collision detection and a two-phase placement strategy.
"""

import math
from dataclasses import dataclass, field

import click
import geopandas as gpd
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.transforms import Bbox
from rtree import index as rtree_index
from shapely.geometry import LineString, MultiLineString, Point

from hugemaps.style import LABELED_ROAD_TYPES, ROAD_PRIORITY, Style


@dataclass
class PlacedLabel:
    """A label that has been placed on the map."""

    text: str
    x: float
    y: float
    angle: float  # degrees
    font_size: float
    bold: bool
    bbox: tuple[float, float, float, float]  # minx, miny, maxx, maxy
    road_class: str = ""


class LabelPlacer:
    """Manages label placement with R-tree collision detection.

    Guarantees 100% coverage: every named road gets at least one label.
    """

    def __init__(self, style: Style):
        self.style = style
        self._idx = rtree_index.Index()
        self._label_id = 0
        self.placed: list[PlacedLabel] = []
        self.total_named = 0
        self.total_placed = 0

    def _next_id(self) -> int:
        self._label_id += 1
        return self._label_id

    def _estimate_bbox(
        self,
        x: float,
        y: float,
        text: str,
        font_size: float,
        angle_deg: float,
        scale: float,
    ) -> tuple[float, float, float, float]:
        """Estimate the bounding box of a text label in data coordinates.

        Args:
            scale: meters per point (data units per font point)
        """
        # Approximate text dimensions
        char_width = font_size * scale * 0.55
        text_width = len(text) * char_width
        text_height = font_size * scale * 1.3

        angle_rad = math.radians(angle_deg)
        cos_a = abs(math.cos(angle_rad))
        sin_a = abs(math.sin(angle_rad))

        # Rotated bounding box dimensions
        box_w = text_width * cos_a + text_height * sin_a
        box_h = text_width * sin_a + text_height * cos_a

        # Add padding
        pad = text_height * 0.3
        return (
            x - box_w / 2 - pad,
            y - box_h / 2 - pad,
            x + box_w / 2 + pad,
            y + box_h / 2 + pad,
        )

    def _has_collision(self, bbox: tuple[float, float, float, float]) -> bool:
        """Check if a bbox collides with any already-placed label."""
        hits = list(self._idx.intersection(bbox))
        return len(hits) > 0

    def _insert_label(self, label: PlacedLabel) -> None:
        """Insert a placed label into the spatial index."""
        lid = self._next_id()
        self._idx.insert(lid, label.bbox)
        self.placed.append(label)

    def _get_position_along_line(
        self, geom, fraction: float
    ) -> tuple[float, float, float] | None:
        """Get (x, y, angle_degrees) at a fraction along a line geometry."""
        if geom.is_empty:
            return None

        if isinstance(geom, MultiLineString):
            # Use the longest component
            longest = max(geom.geoms, key=lambda g: g.length)
            geom = longest

        if not isinstance(geom, LineString) or geom.length == 0:
            return None

        pt = geom.interpolate(fraction, normalized=True)
        x, y = pt.x, pt.y

        # Calculate angle from nearby points
        d = min(geom.length * 0.05, 50)  # 5% of length or 50m
        d = max(d, 1.0)
        frac_m = fraction * geom.length
        p1 = geom.interpolate(max(0, frac_m - d))
        p2 = geom.interpolate(min(geom.length, frac_m + d))

        dx = p2.x - p1.x
        dy = p2.y - p1.y
        angle = math.degrees(math.atan2(dy, dx))

        # Keep text readable (not upside down)
        if angle > 90:
            angle -= 180
        elif angle < -90:
            angle += 180

        return (x, y, angle)

    def place_street_labels(
        self,
        ax: Axes,
        streets_gdf: gpd.GeoDataFrame,
        scale: float,
    ) -> list[PlacedLabel]:
        """Place street name labels with guaranteed 100% coverage.

        Args:
            ax: Matplotlib axes to draw on
            streets_gdf: GeoDataFrame with 'name' and 'road_class' columns, in projected CRS
            scale: meters per inch of the map

        Returns:
            List of placed labels
        """
        if streets_gdf.empty or "name" not in streets_gdf.columns:
            return []

        named = streets_gdf[
            streets_gdf["name"].notna() & (streets_gdf["name"] != "")
        ].copy()
        if named.empty:
            return []

        # Group segments by name and pick best road_class
        road_groups: dict[str, dict] = {}
        for _, row in named.iterrows():
            name = row["name"]
            rc = row.get("road_class", "residential")
            geom = row.geometry

            if name not in road_groups:
                road_groups[name] = {"segments": [], "road_class": rc}

            road_groups[name]["segments"].append(geom)

            # Keep the highest-priority road class
            current_priority = ROAD_PRIORITY.index(road_groups[name]["road_class"]) if road_groups[name]["road_class"] in ROAD_PRIORITY else 99
            new_priority = ROAD_PRIORITY.index(rc) if rc in ROAD_PRIORITY else 99
            if new_priority < current_priority:
                road_groups[name]["road_class"] = rc

        self.total_named = len(road_groups)
        click.echo(f"  Placing labels for {self.total_named:,} unique named roads...")

        # Sort by priority (major roads first)
        def _sort_key(item):
            name, info = item
            rc = info["road_class"]
            pri = ROAD_PRIORITY.index(rc) if rc in ROAD_PRIORITY else 99
            return (pri, name)

        sorted_roads = sorted(road_groups.items(), key=_sort_key)

        # Scale factor: meters per font-point for bbox estimation
        # At 72 points per inch: scale (m/in) / 72 (pt/in) = m/pt
        meters_per_pt = scale / 72.0

        # Phase 1: Guaranteed placement
        placed_names = set()
        forced = 0

        for name, info in sorted_roads:
            rc = info["road_class"]
            segments = info["segments"]
            rs = self.style.get_road_style(rc)

            # Sort segments by length (longest first — best candidates)
            segments.sort(key=lambda g: g.length if hasattr(g, "length") else 0, reverse=True)

            placed = False
            font_size = rs.label_size

            # Try each segment at multiple positions
            fractions = [0.5, 0.35, 0.65, 0.25, 0.75, 0.15, 0.85]

            for seg in segments:
                if placed:
                    break
                for frac in fractions:
                    pos = self._get_position_along_line(seg, frac)
                    if pos is None:
                        continue

                    x, y, angle = pos
                    bbox = self._estimate_bbox(x, y, name, font_size, angle, meters_per_pt)

                    if not self._has_collision(bbox):
                        label = PlacedLabel(
                            text=name, x=x, y=y, angle=angle,
                            font_size=font_size, bold=rs.label_bold,
                            bbox=bbox, road_class=rc,
                        )
                        self._insert_label(label)
                        placed_names.add(name)
                        placed = True
                        break

            # Force-place if still not placed (shrink font, try offsets)
            if not placed:
                for shrink in [0.85, 0.70, 0.55]:
                    if placed:
                        break
                    reduced_size = font_size * shrink
                    for seg in segments[:3]:
                        if placed:
                            break
                        for frac in fractions:
                            pos = self._get_position_along_line(seg, frac)
                            if pos is None:
                                continue
                            x, y, angle = pos

                            # Try with offset perpendicular to road
                            for offset_mult in [0, 1.5, -1.5, 3.0, -3.0]:
                                offset = offset_mult * reduced_size * meters_per_pt
                                ox = x - offset * math.sin(math.radians(angle))
                                oy = y + offset * math.cos(math.radians(angle))

                                bbox = self._estimate_bbox(
                                    ox, oy, name, reduced_size, angle, meters_per_pt
                                )

                                if not self._has_collision(bbox):
                                    label = PlacedLabel(
                                        text=name, x=ox, y=oy, angle=angle,
                                        font_size=reduced_size, bold=rs.label_bold,
                                        bbox=bbox, road_class=rc,
                                    )
                                    self._insert_label(label)
                                    placed_names.add(name)
                                    placed = True
                                    forced += 1
                                    break

            # Absolute last resort: force-place at midpoint of longest segment
            if not placed and segments:
                seg = segments[0]
                pos = self._get_position_along_line(seg, 0.5)
                if pos:
                    x, y, angle = pos
                    reduced_size = font_size * 0.5
                    bbox = self._estimate_bbox(x, y, name, reduced_size, angle, meters_per_pt)
                    label = PlacedLabel(
                        text=name, x=x, y=y, angle=angle,
                        font_size=reduced_size, bold=False,
                        bbox=bbox, road_class=rc,
                    )
                    self._insert_label(label)
                    placed_names.add(name)
                    forced += 1

        self.total_placed = len(placed_names)

        # Phase 2: Density fill — repeat labels for long roads
        repeat_count = 0
        for name, info in sorted_roads:
            rc = info["road_class"]
            segments = info["segments"]
            rs = self.style.get_road_style(rc)

            # Only repeat for roads with total length > threshold
            total_length = sum(
                s.length for s in segments if hasattr(s, "length")
            )

            # Repeat every ~2000m of road length — enough to see it in each
            # grid cell but not so much that it clutters
            repeat_interval_m = 2000
            num_repeats = int(total_length / repeat_interval_m) - 1

            if num_repeats <= 0:
                continue

            # Merge all segments and sample positions
            all_positions = []
            for seg in segments:
                if not hasattr(seg, "length") or seg.length < 300:
                    continue
                n_samples = max(1, int(seg.length / repeat_interval_m))
                for i in range(n_samples):
                    frac = (i + 0.5) / n_samples
                    pos = self._get_position_along_line(seg, frac)
                    if pos:
                        all_positions.append(pos)

            for x, y, angle in all_positions[:min(num_repeats, 5)]:
                bbox = self._estimate_bbox(
                    x, y, name, rs.label_size, angle, meters_per_pt
                )
                if not self._has_collision(bbox):
                    label = PlacedLabel(
                        text=name, x=x, y=y, angle=angle,
                        font_size=rs.label_size, bold=rs.label_bold,
                        bbox=bbox, road_class=rc,
                    )
                    self._insert_label(label)
                    repeat_count += 1

        click.echo(
            f"  Placed {self.total_placed:,} / {self.total_named:,} street labels "
            f"({self.total_placed / self.total_named * 100:.0f}% coverage)"
        )
        if forced:
            click.echo(f"    ({forced} labels required font reduction)")
        if repeat_count:
            click.echo(f"    ({repeat_count} repeat labels added for long roads)")

        # Render all labels
        self._render_labels(ax)

        return self.placed

    def place_neighborhood_labels(
        self,
        ax: Axes,
        neighborhoods_gdf: gpd.GeoDataFrame,
        scale: float,
    ) -> list[PlacedLabel]:
        """Place neighborhood/suburb name labels."""
        if neighborhoods_gdf.empty:
            return []

        if "name" not in neighborhoods_gdf.columns:
            return []

        named = neighborhoods_gdf[
            neighborhoods_gdf["name"].notna() & (neighborhoods_gdf["name"] != "")
        ]
        if named.empty:
            return []

        meters_per_pt = scale / 72.0
        placed_count = 0

        for _, row in named.iterrows():
            name = row["name"].upper()
            geom = row.geometry

            # Get centroid
            if hasattr(geom, "centroid"):
                pt = geom.centroid
            elif isinstance(geom, Point):
                pt = geom
            else:
                continue

            x, y = pt.x, pt.y
            font_size = self.style.neighborhood_font_size

            # Try placement with shrinking
            placed = False
            for shrink in [1.0, 0.85, 0.70]:
                fs = font_size * shrink
                bbox = self._estimate_bbox(x, y, name, fs, 0, meters_per_pt)

                if not self._has_collision(bbox):
                    label = PlacedLabel(
                        text=name, x=x, y=y, angle=0,
                        font_size=fs, bold=True,
                        bbox=bbox, road_class="neighborhood",
                    )
                    self._insert_label(label)
                    placed_count += 1
                    placed = True
                    break

            # Force-place with offset if needed
            if not placed:
                for dx_mult, dy_mult in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    offset = font_size * meters_per_pt * 3
                    nx = x + dx_mult * offset
                    ny = y + dy_mult * offset
                    fs = font_size * 0.70
                    bbox = self._estimate_bbox(nx, ny, name, fs, 0, meters_per_pt)
                    if not self._has_collision(bbox):
                        label = PlacedLabel(
                            text=name, x=nx, y=ny, angle=0,
                            font_size=fs, bold=True,
                            bbox=bbox, road_class="neighborhood",
                        )
                        self._insert_label(label)
                        placed_count += 1
                        placed = True
                        break

        click.echo(f"  Placed {placed_count} neighborhood labels")
        return self.placed

    def _render_labels(self, ax: Axes) -> None:
        """Render all placed labels onto the axes."""
        halo = [
            pe.withStroke(
                linewidth=self.style.label_halo_width,
                foreground=self.style.label_halo_color,
            )
        ]

        for label in self.placed:
            if label.road_class == "neighborhood":
                ax.text(
                    label.x, label.y, label.text,
                    fontsize=label.font_size,
                    fontfamily=self.style.font_family,
                    fontweight="bold",
                    color=self.style.neighborhood_font_color,
                    alpha=self.style.neighborhood_font_alpha,
                    ha="center", va="center",
                    rotation=0,
                    zorder=50,
                    path_effects=halo,
                    fontstyle="normal",
                    fontstretch="expanded",
                )
            else:
                ax.text(
                    label.x, label.y, label.text,
                    fontsize=label.font_size,
                    fontfamily=self.style.font_family,
                    fontweight="bold" if label.bold else "normal",
                    color=self.style.label_color,
                    ha="center", va="center",
                    rotation=label.angle,
                    rotation_mode="anchor",
                    zorder=45,
                    path_effects=halo,
                )

    def render_neighborhood_labels(self, ax: Axes) -> None:
        """Render only the neighborhood labels (called separately after streets)."""
        halo = [
            pe.withStroke(
                linewidth=self.style.label_halo_width + 1,
                foreground=self.style.label_halo_color,
            )
        ]
        for label in self.placed:
            if label.road_class == "neighborhood":
                ax.text(
                    label.x, label.y, label.text,
                    fontsize=label.font_size,
                    fontfamily=self.style.font_family,
                    fontweight="bold",
                    color=self.style.neighborhood_font_color,
                    alpha=self.style.neighborhood_font_alpha,
                    ha="center", va="center",
                    rotation=0,
                    zorder=50,
                    path_effects=halo,
                )
