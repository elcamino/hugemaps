"""PDF and SVG export with proper sizing and font embedding."""

from pathlib import Path

import click
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.figure import Figure


def export_pdf(fig: Figure, output_path: str | Path, dpi: int = 300) -> Path:
    """Export the figure as a print-ready PDF with embedded fonts.

    Args:
        fig: The rendered matplotlib figure
        output_path: Path for the output PDF file
        dpi: Resolution (default 300 for print quality)

    Returns:
        Path to the created file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Ensure fonts are embedded as Type 42 (TrueType) for best compatibility
    matplotlib.rcParams["pdf.fonttype"] = 42
    matplotlib.rcParams["ps.fonttype"] = 42

    click.echo(f"\n  Exporting PDF to: {output_path}")
    click.echo(f"    Size: {fig.get_figwidth():.1f} x {fig.get_figheight():.1f} inches @ {dpi} DPI")

    fig.savefig(
        str(output_path),
        format="pdf",
        dpi=dpi,
        bbox_inches="tight",
        pad_inches=0.2,
        facecolor=fig.get_facecolor(),
        edgecolor="none",
    )

    size_mb = output_path.stat().st_size / (1024 * 1024)
    click.echo(f"    PDF saved: {size_mb:.1f} MB")
    return output_path


def export_svg(fig: Figure, output_path: str | Path) -> Path:
    """Export the figure as an SVG (vector, resolution-independent).

    Args:
        fig: The rendered matplotlib figure
        output_path: Path for the output SVG file

    Returns:
        Path to the created file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # SVG settings
    matplotlib.rcParams["svg.fonttype"] = "none"  # Use text elements, not paths

    click.echo(f"\n  Exporting SVG to: {output_path}")
    click.echo(f"    Size: {fig.get_figwidth():.1f} x {fig.get_figheight():.1f} inches")

    fig.savefig(
        str(output_path),
        format="svg",
        bbox_inches="tight",
        pad_inches=0.2,
        facecolor=fig.get_facecolor(),
        edgecolor="none",
    )

    size_mb = output_path.stat().st_size / (1024 * 1024)
    click.echo(f"    SVG saved: {size_mb:.1f} MB")
    return output_path
