"""Page layout, title block, legend, scale bar, and attribution.

Manages the overall composition of the map page including margins,
title area, legend, and scale bar — styled after the Thomas Bros
page layout with its characteristic bold title and compact legend box.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from hugemaps.style import Style


def create_figure(
    width_in: float,
    height_in: float,
    dpi: int = 300,
) -> tuple[Figure, Axes]:
    """Create the matplotlib figure with proper sizing.

    Returns (fig, map_ax). Title and legend are drawn directly on the figure.
    """
    # Margins for title (top), legend (bottom), and grid labels (sides)
    margin_top = 1.5  # inches for title
    margin_bottom = 1.8  # inches for legend/scale bar/attribution
    margin_side = 1.0  # inches for grid numbers

    total_w = width_in + 2 * margin_side
    total_h = height_in + margin_top + margin_bottom

    fig = plt.figure(figsize=(total_w, total_h), dpi=dpi, facecolor="white")

    # Map axes in the center
    left = margin_side / total_w
    bottom = margin_bottom / total_h
    map_w = width_in / total_w
    map_h = height_in / total_h

    map_ax = fig.add_axes([left, bottom, map_w, map_h])
    map_ax.set_aspect("equal")

    return fig, map_ax


def draw_title(
    fig: Figure,
    city_name: str,
    style: Style,
    map_bounds_fig: tuple[float, float, float, float] | None = None,
) -> None:
    """Draw a bold title block at the top of the page."""
    display_name = city_name.split(",")[0].strip().upper()
    subtitle = city_name.strip()

    # Title background band
    fig_h = fig.get_figheight()
    band_height = 1.2 / fig_h  # ~1.2 inches
    fig.patches.append(mpatches.FancyBboxPatch(
        (0.0, 1.0 - band_height),
        1.0,
        band_height,
        boxstyle="square,pad=0",
        facecolor="#2C3E50",
        edgecolor="none",
        transform=fig.transFigure,
        clip_on=False,
        zorder=0,
    ))

    fig.text(
        0.5, 1.0 - band_height * 0.3, display_name,
        fontsize=style.title_font_size,
        fontfamily=style.font_family,
        fontweight="bold",
        color="#FFFFFF",
        ha="center", va="center",
        zorder=1,
    )

    fig.text(
        0.5, 1.0 - band_height * 0.72, subtitle,
        fontsize=style.title_font_size * 0.38,
        fontfamily=style.font_family,
        fontweight="normal",
        color="#B0BEC5",
        ha="center", va="center",
        zorder=1,
    )


def draw_legend(fig: Figure, style: Style) -> None:
    """Draw a compact legend box showing road types and feature colors."""
    fig_w = fig.get_figwidth()
    fig_h = fig.get_figheight()

    # Legend box — positioned at bottom left
    box_x = 0.03
    box_y = 0.008
    box_w = 0.55
    box_h = 1.3 / fig_h  # ~1.3 inches

    # Background box
    fig.patches.append(mpatches.FancyBboxPatch(
        (box_x, box_y),
        box_w,
        box_h,
        boxstyle="round,pad=0.008",
        facecolor="#FFFFFF",
        edgecolor="#AAAAAA",
        linewidth=0.8,
        transform=fig.transFigure,
        clip_on=False,
    ))

    # Title
    fig.text(
        box_x + 0.01, box_y + box_h - 0.008, "LEGEND",
        fontsize=style.legend_font_size + 1,
        fontfamily=style.font_family,
        fontweight="bold",
        color="#333333",
        ha="left", va="top",
    )

    # Road types — two rows
    road_items = [
        ("Freeway", style.road_styles["motorway"].fill_color, style.road_styles["motorway"].casing_color, 6.0, 9.0),
        ("Major Road", style.road_styles["trunk"].fill_color, style.road_styles["trunk"].casing_color, 5.0, 7.5),
        ("Primary", style.road_styles["primary"].fill_color, style.road_styles["primary"].casing_color, 4.0, 6.0),
        ("Secondary", style.road_styles["secondary"].fill_color, style.road_styles["secondary"].casing_color, 3.0, 4.5),
        ("Local", style.road_styles["residential"].fill_color, style.road_styles["residential"].casing_color, 2.5, 3.5),
    ]

    area_items = [
        ("Park", style.park_color, style.park_edge_color),
        ("Water", style.water_color, style.water_edge_color),
        ("Building", style.building_color, style.building_edge_color),
    ]

    col_w = 0.095
    row1_y = box_y + box_h * 0.42
    row2_y = box_y + box_h * 0.1

    # Road entries — draw casing + fill lines directly on figure
    for i, (label, fill, casing, fill_w, cas_w) in enumerate(road_items):
        x = box_x + 0.015 + i * col_w
        line_y = row1_y + 0.012
        line_x1 = x + 0.005
        line_x2 = x + col_w - 0.01

        # Casing line (background/outline)
        fig.lines.append(mlines.Line2D(
            [line_x1, line_x2], [line_y, line_y],
            color=casing,
            linewidth=cas_w,
            solid_capstyle="round",
            transform=fig.transFigure,
            clip_on=False,
        ))
        # Fill line (foreground)
        fig.lines.append(mlines.Line2D(
            [line_x1, line_x2], [line_y, line_y],
            color=fill,
            linewidth=fill_w,
            solid_capstyle="round",
            transform=fig.transFigure,
            clip_on=False,
        ))

        fig.text(
            (line_x1 + line_x2) / 2, row1_y - 0.002, label,
            fontsize=style.legend_font_size,
            fontfamily=style.font_family,
            fontweight="bold",
            color="#333333",
            ha="center", va="top",
        )

    # Area feature entries — draw filled rectangles
    for i, (label, fill, edge) in enumerate(area_items):
        x = box_x + 0.015 + (len(road_items) + i) * col_w
        swatch_y = row1_y + 0.005
        swatch_w = col_w - 0.02
        swatch_h = 0.015

        fig.patches.append(mpatches.FancyBboxPatch(
            (x + 0.005, swatch_y),
            swatch_w,
            swatch_h,
            boxstyle="square,pad=0",
            facecolor=fill,
            edgecolor=edge,
            linewidth=1.0,
            transform=fig.transFigure,
            clip_on=False,
        ))

        fig.text(
            x + 0.005 + swatch_w / 2, row1_y - 0.002, label,
            fontsize=style.legend_font_size,
            fontfamily=style.font_family,
            fontweight="bold",
            color="#333333",
            ha="center", va="top",
        )


def draw_scale_bar(
    fig: Figure,
    scale_m_per_inch: float,
    style: Style,
) -> None:
    """Draw a scale bar at the bottom right."""
    bar_inches = 2.0
    bar_meters = bar_inches * scale_m_per_inch

    nice_distances = [100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000]
    bar_distance = min(nice_distances, key=lambda d: abs(d - bar_meters))
    bar_actual_inches = bar_distance / scale_m_per_inch

    fig_w = fig.get_figwidth()
    fig_h = fig.get_figheight()

    x_start = 0.70
    y_pos = 0.035
    bar_fig_w = bar_actual_inches / fig_w

    # Alternating black/white segments (Thomas Bros style scale bar)
    n_segments = 4
    seg_w = bar_fig_w / n_segments
    for i in range(n_segments):
        color = "#333333" if i % 2 == 0 else "#FFFFFF"
        fig.patches.append(mpatches.FancyBboxPatch(
            (x_start + i * seg_w, y_pos - 0.004),
            seg_w,
            0.008,
            boxstyle="square,pad=0",
            facecolor=color,
            edgecolor="#333333",
            linewidth=0.5,
            transform=fig.transFigure,
            clip_on=False,
        ))

    if bar_distance >= 1000:
        label = f"{bar_distance / 1000:.0f} km"
    else:
        label = f"{bar_distance} m"

    fig.text(
        x_start, y_pos - 0.013, "0",
        fontsize=8, fontfamily=style.font_family,
        fontweight="bold", color="#333333",
        ha="center", va="top",
    )
    fig.text(
        x_start + bar_fig_w, y_pos - 0.013, label,
        fontsize=8, fontfamily=style.font_family,
        fontweight="bold", color="#333333",
        ha="center", va="top",
    )
    fig.text(
        x_start + bar_fig_w / 2, y_pos + 0.012, "SCALE",
        fontsize=7, fontfamily=style.font_family,
        fontweight="bold", color="#555555",
        ha="center", va="bottom",
    )


def draw_attribution(fig: Figure, style: Style) -> None:
    """Draw OSM attribution text."""
    fig.text(
        0.5, 0.003,
        "Map data \u00A9 OpenStreetMap contributors  \u2022  Generated by HugeMaps",
        fontsize=7,
        fontfamily=style.font_family,
        color="#777777",
        ha="center", va="bottom",
    )
