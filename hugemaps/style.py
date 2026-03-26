"""Thomas Bros map style configuration.

Defines the color palette, road widths, font sizes, and other visual parameters
that recreate the look of Thomas Bros / Thomas Guide maps from the 2000s era.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RoadStyle:
    """Visual style for a road classification."""

    fill_color: str
    casing_color: str | None  # None = no casing
    fill_width: float  # points
    casing_width: float  # points (total width including casing)
    label_size: float  # font size in points
    label_bold: bool = False
    zorder_casing: int = 1
    zorder_fill: int = 2
    dash: tuple | None = None  # None = solid


@dataclass(frozen=True)
class Style:
    """Complete Thomas Bros map style."""

    # Background
    background: str = "#F5F0E1"  # warm cream

    # Feature colors
    park_color: str = "#C8E6A0"
    park_edge_color: str = "#A0C878"
    water_color: str = "#A8D4E6"
    water_edge_color: str = "#78B0CC"
    building_color: str = "#D8D0C0"
    building_edge_color: str = "#C0B8A8"
    railway_color: str = "#666666"
    boundary_color: str = "#888888"

    # Road styles by classification (ordered back-to-front)
    road_styles: dict = field(default_factory=lambda: {
        "motorway": RoadStyle(
            fill_color="#E8841A",
            casing_color="#8B4513",
            fill_width=3.0,
            casing_width=4.2,
            label_size=10.0,
            label_bold=True,
            zorder_casing=10,
            zorder_fill=11,
        ),
        "motorway_link": RoadStyle(
            fill_color="#E8841A",
            casing_color="#8B4513",
            fill_width=1.8,
            casing_width=2.6,
            label_size=7.0,
            label_bold=False,
            zorder_casing=10,
            zorder_fill=11,
        ),
        "trunk": RoadStyle(
            fill_color="#F0C040",
            casing_color="#B8860B",
            fill_width=2.5,
            casing_width=3.5,
            label_size=9.5,
            label_bold=True,
            zorder_casing=8,
            zorder_fill=9,
        ),
        "trunk_link": RoadStyle(
            fill_color="#F0C040",
            casing_color="#B8860B",
            fill_width=1.5,
            casing_width=2.2,
            label_size=7.0,
            label_bold=False,
            zorder_casing=8,
            zorder_fill=9,
        ),
        "primary": RoadStyle(
            fill_color="#FFFFFF",
            casing_color="#999999",
            fill_width=2.0,
            casing_width=3.0,
            label_size=9.0,
            label_bold=True,
            zorder_casing=6,
            zorder_fill=7,
        ),
        "primary_link": RoadStyle(
            fill_color="#FFFFFF",
            casing_color="#999999",
            fill_width=1.2,
            casing_width=1.8,
            label_size=7.0,
            label_bold=False,
            zorder_casing=6,
            zorder_fill=7,
        ),
        "secondary": RoadStyle(
            fill_color="#FFFFFF",
            casing_color="#BBBBBB",
            fill_width=1.6,
            casing_width=2.4,
            label_size=8.0,
            label_bold=False,
            zorder_casing=5,
            zorder_fill=5,
        ),
        "secondary_link": RoadStyle(
            fill_color="#FFFFFF",
            casing_color="#BBBBBB",
            fill_width=1.0,
            casing_width=1.6,
            label_size=7.0,
            label_bold=False,
            zorder_casing=5,
            zorder_fill=5,
        ),
        "tertiary": RoadStyle(
            fill_color="#FFFFFF",
            casing_color="#CCCCCC",
            fill_width=1.2,
            casing_width=1.8,
            label_size=7.5,
            label_bold=False,
            zorder_casing=4,
            zorder_fill=4,
        ),
        "tertiary_link": RoadStyle(
            fill_color="#FFFFFF",
            casing_color="#CCCCCC",
            fill_width=0.8,
            casing_width=1.2,
            label_size=6.5,
            label_bold=False,
            zorder_casing=4,
            zorder_fill=4,
        ),
        "residential": RoadStyle(
            fill_color="#FFFFFF",
            casing_color=None,
            fill_width=0.7,
            casing_width=0.7,
            label_size=6.0,
            label_bold=False,
            zorder_casing=3,
            zorder_fill=3,
        ),
        "living_street": RoadStyle(
            fill_color="#FFFFFF",
            casing_color=None,
            fill_width=0.6,
            casing_width=0.6,
            label_size=5.5,
            label_bold=False,
            zorder_casing=3,
            zorder_fill=3,
        ),
        "unclassified": RoadStyle(
            fill_color="#FFFFFF",
            casing_color=None,
            fill_width=0.6,
            casing_width=0.6,
            label_size=6.0,
            label_bold=False,
            zorder_casing=3,
            zorder_fill=3,
        ),
        "service": RoadStyle(
            fill_color="#E8E0D0",
            casing_color=None,
            fill_width=0.3,
            casing_width=0.3,
            label_size=5.0,
            label_bold=False,
            zorder_casing=2,
            zorder_fill=2,
        ),
        "pedestrian": RoadStyle(
            fill_color="#E8E0D0",
            casing_color=None,
            fill_width=0.4,
            casing_width=0.4,
            label_size=5.5,
            label_bold=False,
            zorder_casing=2,
            zorder_fill=2,
        ),
    })

    # Neighborhood / suburb labels
    neighborhood_font_size: float = 16.0
    neighborhood_font_color: str = "#444444"
    neighborhood_font_alpha: float = 0.6

    # Grid reference
    grid_line_color: str = "#AAAAAA"
    grid_line_width: float = 0.4
    grid_line_alpha: float = 0.4
    grid_label_size: float = 11.0
    grid_label_color: str = "#555555"

    # Title
    title_font_size: float = 28.0
    title_font_color: str = "#333333"

    # Legend
    legend_font_size: float = 9.0

    # Scale bar
    scale_bar_color: str = "#333333"
    scale_bar_height: float = 0.15  # inches

    # Railway
    railway_width: float = 1.0
    railway_dash: tuple = (4, 3)

    # General font
    font_family: str = "sans-serif"

    # Label placement
    label_color: str = "#222222"
    label_halo_color: str = "#F5F0E1"  # same as background for halo effect
    label_halo_width: float = 2.5  # stroke width for halo

    # Feature rendering
    building_alpha: float = 0.5
    park_alpha: float = 0.7
    water_alpha: float = 0.8

    def get_road_style(self, highway_tag: str) -> RoadStyle:
        """Get the road style for a given highway tag, with fallback."""
        if highway_tag in self.road_styles:
            return self.road_styles[highway_tag]
        # Fallback: treat unknown types as service roads
        return self.road_styles["service"]


# Priority order for road rendering and labeling (highest priority first)
ROAD_PRIORITY = [
    "motorway",
    "motorway_link",
    "trunk",
    "trunk_link",
    "primary",
    "primary_link",
    "secondary",
    "secondary_link",
    "tertiary",
    "tertiary_link",
    "residential",
    "living_street",
    "unclassified",
    "pedestrian",
    "service",
]

# Road types that should always be labeled (skip service/pedestrian for density control)
LABELED_ROAD_TYPES = [
    "motorway",
    "motorway_link",
    "trunk",
    "trunk_link",
    "primary",
    "primary_link",
    "secondary",
    "secondary_link",
    "tertiary",
    "tertiary_link",
    "residential",
    "living_street",
    "unclassified",
    "pedestrian",
    "service",
]
