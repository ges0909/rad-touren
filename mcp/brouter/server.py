"""MCP server for BRouter cycling routing with GPX map and elevation rendering.

Uses lib.brouter for route calculation and geocoding. GPX rendering
(map + elevation profile) is handled here due to file system and image dependencies.
"""

import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import gpxpy
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from fastmcp import FastMCP
from staticmap import StaticMap, IconMarker, Line

# Add lib/ to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from lib.brouter import calculate_route as _lib_calculate_route, search_location as _lib_search_location

mcp = FastMCP("BRouter Cycling Router")

VALID_PROFILES = {
    "trekking",
    "fastbike",
    "trekking-ignore-cr",
    "safety",
    "shortest",
    "trekking-steep",
    "trekking-noferries",
    "trekking-nosteps",
}


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


def validate_waypoints(waypoints: list[list[float]]) -> str | None:
    """Return an error string if waypoints are invalid, else None."""
    if len(waypoints) < 2:
        return "At least 2 waypoints are required."
    return None


def validate_coordinates(lon: float, lat: float) -> str | None:
    """Return an error string if coordinates are out of range, else None."""
    if not (-180 <= lon <= 180):
        return (
            f"Invalid coordinates: [{lon}, {lat}] — "
            "longitude must be between -180 and 180."
        )
    if not (-90 <= lat <= 90):
        return (
            f"Invalid coordinates: [{lon}, {lat}] — "
            "latitude must be between -90 and 90."
        )
    return None


def validate_profile(profile: str) -> str | None:
    """Return an error string if the profile is not supported, else None."""
    if profile not in VALID_PROFILES:
        valid = ", ".join(sorted(VALID_PROFILES))
        return f"Invalid profile '{profile}'. Valid profiles: {valid}"
    return None


def validate_alternativeidx(idx: int) -> str | None:
    """Return an error string if the alternative index is out of range, else None."""
    if idx < 0 or idx > 3:
        return f"Invalid alternative index {idx}. Valid range is 0 to 3."
    return None


# ---------------------------------------------------------------------------
# GPX helpers
# ---------------------------------------------------------------------------

# GPX namespace used by BRouter
_GPX_NS = "http://www.topografix.com/GPX/1/1"


def insert_track_name(gpx_content: str, name: str) -> str:
    """Insert or replace a ``<name>`` element inside the ``<trk>`` element.

    Uses :mod:`xml.etree.ElementTree` for XML manipulation.
    """
    # Register the default namespace so output doesn't get ns0: prefixes
    ET.register_namespace("", _GPX_NS)

    root = ET.fromstring(gpx_content)

    # Find <trk> — try with namespace first, then without
    trk = root.find(f"{{{_GPX_NS}}}trk")
    if trk is None:
        trk = root.find("trk")
    if trk is None:
        return gpx_content  # no <trk> element, return unchanged

    # Look for existing <name> child
    name_elem = trk.find(f"{{{_GPX_NS}}}name")
    if name_elem is None:
        name_elem = trk.find("name")

    if name_elem is None:
        # Create a new <name> element and insert at the beginning of <trk>
        name_elem = ET.SubElement(trk, "name")
        # Move it to be the first child
        trk.remove(name_elem)
        trk.insert(0, name_elem)

    name_elem.text = name

    return ET.tostring(root, encoding="unicode", xml_declaration=True)


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def calculate_route(
    waypoints: list[list[float]],
    profile: str = "trekking",
    format: str = "gpx",
    alternativeidx: int = 0,
    nogos: list[dict] | None = None,
    track_name: str | None = None,
) -> str:
    """Calculate a cycling route through waypoints via the BRouter API.

    Args:
        waypoints: List of [longitude, latitude] coordinate pairs (minimum 2).
        profile: Cycling profile name (default: "trekking"). Valid profiles:
            trekking, fastbike, trekking-ignore-cr, safety, shortest,
            trekking-steep, trekking-noferries, trekking-nosteps.
        format: Output format — "gpx" (default) or "geojson".
        alternativeidx: Alternative route index 0–3 (default: 0).
        nogos: Optional list of no-go areas, each a dict with keys
            "lon", "lat", and optional "radius" (meters, default 20).
        track_name: Optional name to insert into the GPX <trk><name> element.
    """
    # Input validation
    err = validate_waypoints(waypoints)
    if err:
        return err
    for wp in waypoints:
        if len(wp) < 2:
            return f"Invalid waypoint {wp}: each must be [longitude, latitude]."
        err = validate_coordinates(wp[0], wp[1])
        if err:
            return err
    err = validate_profile(profile)
    if err:
        return err
    err = validate_alternativeidx(alternativeidx)
    if err:
        return err

    # Call lib
    result = await _lib_calculate_route(
        waypoints=waypoints,
        profile=profile,
        format=format,
        alternativeidx=alternativeidx,
        nogos=nogos,
    )

    if "error" in result:
        return result["error"]

    content = result["content"]

    # Handle GeoJSON
    if format == "geojson":
        return f"## Route (GeoJSON)\n\n```json\n{content}\n```"

    # Handle GPX
    if "<trk>" not in content and "<trk " not in content:
        return "Error: BRouter returned an invalid GPX response."

    gpx_content = content
    if track_name:
        gpx_content = insert_track_name(gpx_content, track_name)

    return (
        f"## Route Summary\n"
        f"- Distance: {result['distance_km']:.1f} km\n"
        f"- Elevation gain: {result['elevation_gain_m']:.0f} m\n"
        f"- Estimated duration: {result['duration_min']} min\n"
        f"- Profile: {profile}\n"
        f"- Format: gpx\n\n"
        f"## GPX Data\n{gpx_content}"
    )


@mcp.tool()
async def search_location(
    query: str,
    country_code: str = "de",
    limit: int = 5,
) -> str:
    """Search for locations by name via the Nominatim geocoding API.

    Args:
        query: Search query string (place name, address, etc.).
        country_code: ISO 3166-1 alpha-2 country code to restrict results
            (default: "de" for Germany).
        limit: Maximum number of results to return, 1–40 (default: 5).
    """
    result = await _lib_search_location(query, country_code, limit)

    if "error" in result:
        return result["error"]

    results = result["results"]
    if not results:
        return f'No locations found for "{query}".'

    lines = [f'## Search Results for "{query}"\n']
    for i, r in enumerate(results, 1):
        lines.append(
            f"{i}. {r['name']}\n"
            f"   Coordinates: [{r['lon']}, {r['lat']}]\n"
        )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# MCP Tool: render_gpx_map
# ---------------------------------------------------------------------------

# Directory containing Twemoji-based marker icons (CC-BY 4.0)
_ICONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")

# POI category → emoji icon file mapping (4 main categories from steering)
POI_CATEGORY_ICON: dict[str, str] = {
    # 🏛️ Sehenswürdigkeiten
    "museum": "sight.png",
    "castle": "sight.png",
    "memorial": "sight.png",
    "ruins": "sight.png",
    "church": "sight.png",
    "viewpoint": "sight.png",
    # 🎨 Kunst
    "artwork": "art.png",
    "gallery": "art.png",
    # 🍺 Einkehr
    "beer_garden": "food.png",
    "cafe": "food.png",
    "restaurant": "food.png",
    # 🏊 Badestellen
    "swimming": "swim.png",
    # Radservice & Rast → sight as fallback
    "bicycle_repair": "sight.png",
    "drinking_water": "sight.png",
    "picnic": "sight.png",
}

_DEFAULT_ICON = "sight.png"

# Legend entries: (icon_file, label)
_LEGEND_ENTRIES = [
    ("sight.png", "Sehenswürdigkeiten"),
    ("art.png", "Kunst"),
    ("food.png", "Einkehr"),
    ("swim.png", "Badestellen"),
]


def _draw_legend(image: "Image.Image") -> "Image.Image":
    """Draw a small legend box in the bottom-left corner of the map image."""
    from PIL import Image, ImageDraw, ImageFont

    img = image.convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Try to load a decent font, fall back to default
    font = None
    for font_path in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu[wdth,wght].ttf",
    ]:
        if os.path.isfile(font_path):
            try:
                font = ImageFont.truetype(font_path, 12)
                break
            except Exception:
                pass
    if font is None:
        font = ImageFont.load_default()

    icon_size = 16
    padding = 8
    line_height = icon_size + 4
    text_offset_x = icon_size + 6

    # Measure legend dimensions
    max_text_width = 0
    for _, label in _LEGEND_ENTRIES:
        bbox = draw.textbbox((0, 0), label, font=font)
        max_text_width = max(max_text_width, bbox[2] - bbox[0])

    legend_w = padding + text_offset_x + max_text_width + padding
    legend_h = padding + len(_LEGEND_ENTRIES) * line_height + padding - 4

    # Position: bottom-left
    x0 = 10
    y0 = img.height - legend_h - 10

    # Semi-transparent white background with rounded feel
    draw.rectangle(
        [x0, y0, x0 + legend_w, y0 + legend_h],
        fill=(255, 255, 255, 210),
        outline=(180, 180, 180, 255),
        width=1,
    )

    # Draw each legend entry
    for i, (icon_file, label) in enumerate(_LEGEND_ENTRIES):
        ey = y0 + padding + i * line_height
        icon_path = os.path.join(_ICONS_DIR, icon_file)
        if os.path.isfile(icon_path):
            try:
                icon = Image.open(icon_path).convert("RGBA")
                icon = icon.resize((icon_size, icon_size), Image.LANCZOS)
                overlay.paste(icon, (x0 + padding, ey), icon)
            except Exception:
                pass
        draw.text(
            (x0 + padding + text_offset_x, ey + 1),
            label,
            fill=(50, 50, 50, 255),
            font=font,
        )

    result = Image.alpha_composite(img, overlay)
    return result.convert("RGB")


@mcp.tool()
async def render_gpx_map(
    gpx_path: str,
    output_path: str,
    width: int = 800,
    height: int = 600,
    line_color: str = "#0066CC",
    line_width: int = 3,
    pois: list[dict] | None = None,
) -> str:
    """Render a GPX track as a PNG map image with OpenStreetMap tiles.

    Args:
        gpx_path: Path to the GPX file to render.
        output_path: Path where the PNG image will be saved.
        width: Image width in pixels (default: 800).
        height: Image height in pixels (default: 600).
        line_color: Route line color as hex string (default: "#0066CC").
        line_width: Route line width in pixels (default: 3).
        pois: Optional list of POIs to render as colored markers on the map.
            Each POI is a dict with keys:
            - "lat" (float, required): Latitude of the POI.
            - "lon" (float, required): Longitude of the POI.
            - "category" (str, optional): POI category for color coding.
              Valid categories: museum, castle, memorial, ruins, church,
              viewpoint, artwork, gallery, beer_garden, cafe, restaurant,
              swimming, bicycle_repair, drinking_water, picnic.
            - "name" (str, optional): Name of the POI (for the summary).

    Returns:
        Success message with output path, or a descriptive error message.
    """
    # Validate input file exists
    if not os.path.isfile(gpx_path):
        return f"Error: GPX file not found: {gpx_path}"

    try:
        with open(gpx_path, "r", encoding="utf-8") as f:
            gpx = gpxpy.parse(f)
    except Exception as exc:
        return f"Error parsing GPX file: {exc}"

    # Collect all trackpoints
    coordinates: list[tuple[float, float]] = []
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                coordinates.append((point.longitude, point.latitude))

    if len(coordinates) < 2:
        return "Error: GPX file contains fewer than 2 trackpoints."

    # Create static map and add the route line
    m = StaticMap(width, height, padding_x=20, padding_y=20)
    line = Line(coordinates, line_color, line_width)
    m.add_line(line)

    # Add POI markers
    poi_count = 0
    if pois:
        for poi in pois:
            lat = poi.get("lat")
            lon = poi.get("lon")
            if lat is None or lon is None:
                continue
            category = poi.get("category", "")
            icon_file = POI_CATEGORY_ICON.get(category, _DEFAULT_ICON)
            icon_path = os.path.join(_ICONS_DIR, icon_file)
            if not os.path.isfile(icon_path):
                continue
            marker = IconMarker((lon, lat), icon_path, 9, 9)
            m.add_marker(marker)
            poi_count += 1

    try:
        image = m.render()
    except Exception as exc:
        return f"Error rendering map: {exc}"

    # Draw legend overlay if POIs were added
    if poi_count > 0:
        image = _draw_legend(image)

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    try:
        image.save(output_path)
    except Exception as exc:
        return f"Error saving image: {exc}"

    poi_info = f", {poi_count} POI markers" if poi_count else ""
    return f"Map rendered successfully: {output_path} ({width}x{height}px, {len(coordinates)} trackpoints{poi_info})"


# ---------------------------------------------------------------------------
# MCP Tool: render_elevation_profile
# ---------------------------------------------------------------------------


@mcp.tool()
async def render_elevation_profile(
    gpx_path: str,
    output_path: str,
    width: int = 800,
    height: int = 300,
) -> str:
    """Render an elevation profile chart from a GPX track as a PNG image.

    Args:
        gpx_path: Path to the GPX file to render.
        output_path: Path where the PNG image will be saved.
        width: Image width in pixels (default: 800).
        height: Image height in pixels (default: 300).

    Returns:
        Success message with stats, or a descriptive error message.
    """
    if not os.path.isfile(gpx_path):
        return f"Error: GPX file not found: {gpx_path}"

    try:
        with open(gpx_path, "r", encoding="utf-8") as f:
            gpx = gpxpy.parse(f)
    except Exception as exc:
        return f"Error parsing GPX file: {exc}"

    # Collect distances and elevations
    distances: list[float] = []
    elevations: list[float] = []
    cumulative_dist = 0.0

    for track in gpx.tracks:
        for segment in track.segments:
            prev_point = None
            for point in segment.points:
                if point.elevation is None:
                    continue
                if prev_point is not None:
                    cumulative_dist += point.distance_2d(prev_point)
                distances.append(cumulative_dist / 1000.0)  # km
                elevations.append(point.elevation)
                prev_point = point

    if len(distances) < 2:
        return "Error: GPX file contains fewer than 2 points with elevation data."

    # Calculate stats
    min_ele = min(elevations)
    max_ele = max(elevations)
    total_ascent = sum(
        elevations[i] - elevations[i - 1]
        for i in range(1, len(elevations))
        if elevations[i] > elevations[i - 1]
    )
    total_descent = sum(
        elevations[i - 1] - elevations[i]
        for i in range(1, len(elevations))
        if elevations[i] < elevations[i - 1]
    )

    # Render chart
    dpi = 100
    fig, ax = plt.subplots(figsize=(width / dpi, height / dpi), dpi=dpi)
    ax.fill_between(distances, elevations, alpha=0.3, color="#0066CC")
    ax.plot(distances, elevations, color="#0066CC", linewidth=1.5)
    ax.set_xlabel("Distanz (km)")
    ax.set_ylabel("Höhe (m)")
    ax.set_xlim(distances[0], distances[-1])
    ele_range = max_ele - min_ele
    ax.set_ylim(min_ele - max(ele_range * 0.1, 5), max_ele + max(ele_range * 0.1, 5))
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    # Save
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    try:
        fig.savefig(output_path, dpi=dpi)
    except Exception as exc:
        return f"Error saving image: {exc}"
    finally:
        plt.close(fig)

    return (
        f"Elevation profile rendered: {output_path} ({width}x{height}px, "
        f"{distances[-1]:.1f} km, {min_ele:.0f}–{max_ele:.0f} m, "
        f"↑{total_ascent:.0f} m ↓{total_descent:.0f} m)"
    )


if __name__ == "__main__":
    mcp.run()
