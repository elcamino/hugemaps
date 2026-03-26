"""Page layout, title block, legend, scale bar, and attribution.

Manages the overall composition of the map page including margins,
title area, legend, and scale bar.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from hugemaps.style import ROAD_PRIORITY, Style


def create_figure(
    width_in: float,
    height_in: float,
    dpi: int = 300,
) -> tuple[Figure, Axes]:
    """Create the matplotlib figure with proper sizing.

    Returns (fig, map_ax). Title and legend are drawn directly on the figure
    using fig.text() to avoid axis coordinate issues.
    """
    # Add margins for title (top), legend (bottom), and grid labels (sides)
    margin_top = 1.2  # inches for title
    margin_bottom = 1.5  # inches for legend/scale bar/attribution
    margin_side = 0.8  # inches for grid numbers

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
    """Draw the title at the top of the page."""
    # Clean up city name for display
    display_name = city_name.split(",")[0].strip().upper()
    subtitle = city_name.strip()

    fig.text(
        0.5, 0.97, display_name,
        fontsize=style.title_font_size,
        fontfamily=style.font_family,
        fontweight="bold",
        color=style.title_font_color,
        ha="center", va="top",
    )

    fig.text(
        0.5, 0.97 - style.title_font_size / (fig.get_figheight() * 72) * 1.3,
        subtitle,
        fontsize=style.title_font_size * 0.45,
        fontfamily=style.font_family,
        fontweight="normal",
        color="#666666",
        ha="center", va="top",
    )


def draw_legend(fig: Figure, style: Style) -> None:
    """Draw a legend showing road types and feature colors."""
    legend_items = [
        ("Freeway", style.road_styles["motorway"].fill_color, style.road_styles["motorway"].casing_color, 3.0),
        ("Major Road", style.road_styles["trunk"].fill_color, style.road_styles["trunk"].casing_color, 2.5),
        ("Primary", style.road_styles["primary"].fill_color, style.road_styles["primary"].casing_color, 2.0),
        ("Secondary", style.road_styles["secondary"].fill_color, style.road_styles["secondary"].casing_color, 1.5),
        ("Local Street", style.road_styles["residential"].fill_color, None, 1.0),
        ("Park", style.park_color, style.park_edge_color, None),
        ("Water", style.water_color, style.water_edge_color, None),
        ("Building", style.building_color, style.building_edge_color, None),
    ]

    x_start = 0.05
    y_pos = 0.025
    item_width = 0.11

    for i, (label, fill, edge, width) in enumerate(legend_items):
        x = x_start + i * item_width

        if width is not None:
            # Road type — draw a line
            fig.text(
                x + 0.04, y_pos + 0.008, "———",
                fontsize=8,
                color=fill,
                fontweight="bold",
                ha="center", va="center",
            )
        else:
            # Area feature — draw a small square
            ax_legend = fig.add_axes([x + 0.015, y_pos + 0.002, 0.015, 0.012])
            ax_legend.add_patch(mpatches.Rectangle(
                (0, 0), 1, 1,
                facecolor=fill,
                edgecolor=edge or fill,
                linewidth=0.5,
            ))
            ax_legend.set_xlim(0, 1)
            ax_legend.set_ylim(0, 1)
            ax_legend.axis("off")

        fig.text(
            x + 0.04, y_pos - 0.008, label,
            fontsize=style.legend_font_size,
            fontfamily=style.font_family,
            color="#444444",
            ha="center", va="top",
        )


def draw_scale_bar(
    fig: Figure,
    scale_m_per_inch: float,
    style: Style,
) -> None:
    """Draw a scale bar at the bottom of the page."""
    # Choose a nice round distance for the bar
    bar_inches = 2.0  # physical inches of the bar on paper
    bar_meters = bar_inches * scale_m_per_inch

    # Round to nice number
    nice_distances = [100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000]
    bar_distance = min(nice_distances, key=lambda d: abs(d - bar_meters))
    bar_actual_inches = bar_distance / scale_m_per_inch

    # Position (figure coordinates)
    x_start = 0.75
    y_pos = 0.03

    # Scale bar line
    fig.patches.append(mpatches.FancyBboxPatch(
        (x_start, y_pos - 0.003),
        bar_actual_inches / fig.get_figwidth(),
        0.006,
        boxstyle="square,pad=0",
        facecolor=style.scale_bar_color,
        edgecolor=style.scale_bar_color,
        transform=fig.transFigure,
        clip_on=False,
    ))

    # Labels
    if bar_distance >= 1000:
        label = f"{bar_distance / 1000:.0f} km"
    else:
        label = f"{bar_distance} m"

    fig.text(
        x_start, y_pos - 0.012, "0",
        fontsize=7, fontfamily=style.font_family,
        color="#444444", ha="center", va="top",
    )
    fig.text(
        x_start + bar_actual_inches / fig.get_figwidth(), y_pos - 0.012,
        label,
        fontsize=7, fontfamily=style.font_family,
        color="#444444", ha="center", va="top",
    )


def draw_attribution(fig: Figure, style: Style) -> None:
    """Draw OSM attribution text."""
    fig.text(
        0.5, 0.005,
        "Map data \u00A9 OpenStreetMap contributors  |  Generated by HugeMaps",
        fontsize=6.5,
        fontfamily=style.font_family,
        color="#888888",
        ha="center", va="bottom",
    )
