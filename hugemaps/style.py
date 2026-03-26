"""Thomas Bros map style configuration.

Defines the color palette, road widths, font sizes, and other visual parameters
that recreate the look of Thomas Bros / Thomas Guide maps from the 2000s era.

Key characteristics of the Thomas Bros style:
- Warm cream/tan paper background
- THICK, bold road corridors — even residential streets are wide white bands
  with visible gray outlines creating a clear street grid
- Freeways are bold orange/red bands with dark brown casings
- Arterials are bright yellow bands with dark outlines
- Primary/secondary roads are wide white bands with gray outlines
- All road types have visible casings (outlines) — this is what creates
  the distinctive "road corridor" look
- Rich, saturated colors for parks (green) and water (blue)
- Prominent grid reference system
- Large, bold neighborhood names
- Clean, readable street labels
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

    # Background — distinctly tan/khaki so white road corridors are unmistakable
    background: str = "#DDD0B0"

    # Feature colors — richer, more saturated than before
    park_color: str = "#B5D98C"
    park_edge_color: str = "#7CB352"
    water_color: str = "#8DC8E8"
    water_edge_color: str = "#5A9BBF"
    building_color: str = "#D5CCBA"
    building_edge_color: str = "#B8AD99"
    railway_color: str = "#555555"
    boundary_color: str = "#777777"

    # Road styles — MUCH thicker than before, every type gets a casing
    # This is the key to the Thomas Bros look: bold road corridors
    road_styles: dict = field(default_factory=lambda: {
        "motorway": RoadStyle(
            fill_color="#E87020",
            casing_color="#6B3310",
            fill_width=8.0,
            casing_width=11.0,
            label_size=14.0,
            label_bold=True,
            zorder_casing=10,
            zorder_fill=11,
        ),
        "motorway_link": RoadStyle(
            fill_color="#E87020",
            casing_color="#6B3310",
            fill_width=5.0,
            casing_width=7.0,
            label_size=10.0,
            label_bold=True,
            zorder_casing=10,
            zorder_fill=11,
        ),
        "trunk": RoadStyle(
            fill_color="#F0C020",
            casing_color="#8B6914",
            fill_width=7.0,
            casing_width=9.5,
            label_size=13.0,
            label_bold=True,
            zorder_casing=8,
            zorder_fill=9,
        ),
        "trunk_link": RoadStyle(
            fill_color="#F0C020",
            casing_color="#8B6914",
            fill_width=4.0,
            casing_width=5.5,
            label_size=10.0,
            label_bold=True,
            zorder_casing=8,
            zorder_fill=9,
        ),
        "primary": RoadStyle(
            fill_color="#FFFFFF",
            casing_color="#666666",
            fill_width=9.0,
            casing_width=12.0,
            label_size=12.0,
            label_bold=True,
            zorder_casing=6,
            zorder_fill=7,
        ),
        "primary_link": RoadStyle(
            fill_color="#FFFFFF",
            casing_color="#666666",
            fill_width=6.0,
            casing_width=8.0,
            label_size=10.0,
            label_bold=True,
            zorder_casing=6,
            zorder_fill=7,
        ),
        "secondary": RoadStyle(
            fill_color="#FFFFFF",
            casing_color="#777777",
            fill_width=8.0,
            casing_width=11.0,
            label_size=11.0,
            label_bold=True,
            zorder_casing=5,
            zorder_fill=5,
        ),
        "secondary_link": RoadStyle(
            fill_color="#FFFFFF",
            casing_color="#777777",
            fill_width=5.0,
            casing_width=7.0,
            label_size=9.0,
            label_bold=False,
            zorder_casing=5,
            zorder_fill=5,
        ),
        "tertiary": RoadStyle(
            fill_color="#FFFFFF",
            casing_color="#777777",
            fill_width=7.0,
            casing_width=10.0,
            label_size=10.0,
            label_bold=False,
            zorder_casing=4,
            zorder_fill=4,
        ),
        "tertiary_link": RoadStyle(
            fill_color="#FFFFFF",
            casing_color="#777777",
            fill_width=5.0,
            casing_width=7.0,
            label_size=9.0,
            label_bold=False,
            zorder_casing=4,
            zorder_fill=4,
        ),
        # KEY: residential streets are UNMISTAKABLE white corridors with dark outlines
        # On a wall-sized figure, these need to be very thick to remain visible
        "residential": RoadStyle(
            fill_color="#FFFFFF",
            casing_color="#777777",
            fill_width=7.0,
            casing_width=10.0,
            label_size=9.5,
            label_bold=False,
            zorder_casing=3,
            zorder_fill=3,
        ),
        "living_street": RoadStyle(
            fill_color="#FFFFFF",
            casing_color="#777777",
            fill_width=6.0,
            casing_width=8.5,
            label_size=9.0,
            label_bold=False,
            zorder_casing=3,
            zorder_fill=3,
        ),
        "unclassified": RoadStyle(
            fill_color="#FFFFFF",
            casing_color="#777777",
            fill_width=6.0,
            casing_width=8.5,
            label_size=9.0,
            label_bold=False,
            zorder_casing=3,
            zorder_fill=3,
        ),
        "service": RoadStyle(
            fill_color="#F0E8D5",
            casing_color="#888888",
            fill_width=3.5,
            casing_width=5.0,
            label_size=8.0,
            label_bold=False,
            zorder_casing=2,
            zorder_fill=2,
        ),
        "pedestrian": RoadStyle(
            fill_color="#F0E8D5",
            casing_color="#888888",
            fill_width=4.0,
            casing_width=5.5,
            label_size=8.5,
            label_bold=False,
            zorder_casing=2,
            zorder_fill=2,
        ),
    })

    # Neighborhood / suburb labels — large, bold, prominent
    neighborhood_font_size: float = 22.0
    neighborhood_font_color: str = "#3A3A3A"
    neighborhood_font_alpha: float = 0.55

    # Grid reference — visible but not competing with roads
    grid_line_color: str = "#9CAABB"
    grid_line_width: float = 0.4
    grid_line_alpha: float = 0.35
    grid_label_size: float = 14.0
    grid_label_color: str = "#3A4A5A"

    # Title — larger
    title_font_size: float = 36.0
    title_font_color: str = "#222222"

    # Legend
    legend_font_size: float = 10.0

    # Scale bar
    scale_bar_color: str = "#333333"
    scale_bar_height: float = 0.15  # inches

    # Railway
    railway_width: float = 1.5
    railway_dash: tuple = (6, 4)

    # General font
    font_family: str = "sans-serif"

    # Label placement — darker text, thicker halo for readability
    label_color: str = "#111111"
    label_halo_color: str = "#FFFFFF"  # white halo since labels sit on white roads
    label_halo_width: float = 4.0

    # Feature rendering — more opaque
    building_alpha: float = 0.6
    park_alpha: float = 0.85
    water_alpha: float = 0.9

    def get_road_style(self, highway_tag: str) -> RoadStyle:
        """Get the road style for a given highway tag, with fallback."""
        if highway_tag in self.road_styles:
            return self.road_styles[highway_tag]
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

# Road types that should always be labeled
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
