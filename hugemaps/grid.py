"""Grid reference system overlay.

Draws an A-J / 1-10 style grid reference system inspired by Thomas Bros maps,
with grid lines and margin labels.
"""

import string

from matplotlib.axes import Axes

from hugemaps.style import Style


def draw_grid(
    ax: Axes,
    bounds: tuple[float, float, float, float],
    style: Style,
    cols: int = 8,
    rows: int = 10,
) -> None:
    """Draw a grid reference overlay on the map axes.

    Args:
        ax: The map axes
        bounds: (minx, miny, maxx, maxy) in data coordinates
        style: Style configuration
        cols: Number of grid columns
        rows: Number of grid rows
    """
    minx, miny, maxx, maxy = bounds
    width = maxx - minx
    height = maxy - miny
    col_width = width / cols
    row_height = height / rows

    # Grid lines — solid thin lines (Thomas Bros style)
    for i in range(1, cols):
        x = minx + i * col_width
        ax.axvline(
            x,
            color=style.grid_line_color,
            linewidth=style.grid_line_width,
            alpha=style.grid_line_alpha,
            zorder=40,
        )

    for i in range(1, rows):
        y = miny + i * row_height
        ax.axhline(
            y,
            color=style.grid_line_color,
            linewidth=style.grid_line_width,
            alpha=style.grid_line_alpha,
            zorder=40,
        )

    # Draw border around the full grid (solid, slightly thicker)
    for side_x in [minx, maxx]:
        ax.axvline(
            side_x,
            color=style.grid_line_color,
            linewidth=style.grid_line_width * 2,
            alpha=style.grid_line_alpha * 1.5,
            zorder=40,
        )
    for side_y in [miny, maxy]:
        ax.axhline(
            side_y,
            color=style.grid_line_color,
            linewidth=style.grid_line_width * 2,
            alpha=style.grid_line_alpha * 1.5,
            zorder=40,
        )

    # Column labels (A, B, C, ...) along top and bottom
    letters = string.ascii_uppercase[:cols]
    margin_y_top = maxy + height * 0.008
    margin_y_bottom = miny - height * 0.008

    for i, letter in enumerate(letters):
        x = minx + (i + 0.5) * col_width
        # Top
        ax.text(
            x, margin_y_top, letter,
            fontsize=style.grid_label_size,
            fontfamily=style.font_family,
            fontweight="bold",
            color=style.grid_label_color,
            ha="center", va="bottom",
            zorder=55,
            clip_on=False,
        )
        # Bottom
        ax.text(
            x, margin_y_bottom, letter,
            fontsize=style.grid_label_size,
            fontfamily=style.font_family,
            fontweight="bold",
            color=style.grid_label_color,
            ha="center", va="top",
            zorder=55,
            clip_on=False,
        )

    # Row labels (1, 2, 3, ...) along left and right
    margin_x_left = minx - width * 0.008
    margin_x_right = maxx + width * 0.008

    for i in range(rows):
        y = miny + (i + 0.5) * row_height
        num = str(rows - i)  # Top row = 1
        # Left
        ax.text(
            margin_x_left, y, num,
            fontsize=style.grid_label_size,
            fontfamily=style.font_family,
            fontweight="bold",
            color=style.grid_label_color,
            ha="right", va="center",
            zorder=55,
            clip_on=False,
        )
        # Right
        ax.text(
            margin_x_right, y, num,
            fontsize=style.grid_label_size,
            fontfamily=style.font_family,
            fontweight="bold",
            color=style.grid_label_color,
            ha="left", va="center",
            zorder=55,
            clip_on=False,
        )
