#!/usr/bin/env python3
"""Render a roadtrip route map as PNG using staticmap.

Usage:
    python scripts/render_roadtrip_map.py <gpx_file> <output_png> \
        [--stations 'Name:lon,lat' ...] \
        [--pois 'category:name:lon,lat' ...]

Example:
    python scripts/render_roadtrip_map.py \
        trips/road/gpx/nordspanien-kueste.gpx \
        trips/road/img/nordspanien-kueste.png \
        --stations 'T1 Bilbao:-2.9253,43.2627' 'T2-3 San Sebastián:-1.9812,43.3183' \
        --pois 'art:Guggenheim:-2.9340,43.2687' 'wine:Bodegas Ysios:-2.5950,42.5680'
"""

import argparse
import math
import xml.etree.ElementTree as ET
from pathlib import Path

from staticmap import StaticMap, Line, CircleMarker
from PIL import Image, ImageDraw, ImageFont


# ---------------------------------------------------------------------------
# POI category colors and legend labels
# ---------------------------------------------------------------------------

ICON_DIR = Path(__file__).parent / "icons"

POI_CATEGORIES = {
    "art": {"color": "#9B59B6", "label": "Kunst & Museen", "icon": "art.png"},
    "hike": {"color": "#27AE60", "label": "Wandern", "icon": "hike.png"},
    "swim": {"color": "#3498DB", "label": "Baden", "icon": "swim.png"},
    "food": {"color": "#E67E22", "label": "Essen & Trinken", "icon": "food.png"},
    "wine": {"color": "#8E44AD", "label": "Weingüter", "icon": "wine.png"},
    "sight": {"color": "#2C3E50", "label": "Sehenswürdigkeiten", "icon": "sight.png"},
    "nature": {"color": "#1ABC9C", "label": "Natur & Parks", "icon": "nature.png"},
    "coffee": {"color": "#795548", "label": "Kaffee", "icon": "coffee.png"},
}

# Icon size on map (pixels)
ICON_SIZE = 18
# Icon size in legend (pixels)
LEGEND_ICON_SIZE = 16


# ---------------------------------------------------------------------------
# GPX parsing
# ---------------------------------------------------------------------------


def parse_gpx(gpx_path: str) -> list[tuple[float, float]]:
    """Parse GPX file and return list of (lon, lat) coordinates."""
    tree = ET.parse(gpx_path)
    root = tree.getroot()
    ns = {"gpx": "http://www.topografix.com/GPX/1/1"}

    coords = []
    for trkpt in root.findall(".//gpx:trkpt", ns):
        lat = float(trkpt.get("lat"))
        lon = float(trkpt.get("lon"))
        coords.append((lon, lat))

    if not coords:
        for rtept in root.findall(".//gpx:rtept", ns):
            lat = float(rtept.get("lat"))
            lon = float(rtept.get("lon"))
            coords.append((lon, lat))

    return coords


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------


def parse_station(station_str: str) -> tuple[str, float, float]:
    """Parse 'Name:lon,lat' string."""
    name, coords = station_str.rsplit(":", 1)
    lon, lat = coords.split(",")
    return name.strip(), float(lon), float(lat)


def parse_poi(poi_str: str) -> tuple[str, str, float, float]:
    """Parse 'category:name:lon,lat' string."""
    parts = poi_str.split(":", 2)
    category = parts[0].strip()
    rest = parts[1] if len(parts) > 1 else ""
    name, coords = rest.rsplit(":", 1) if ":" in rest else (rest, parts[2] if len(parts) > 2 else "")
    # Re-parse: category:name:lon,lat
    pieces = poi_str.split(":")
    category = pieces[0].strip()
    name = pieces[1].strip() if len(pieces) > 2 else ""
    coord_str = pieces[-1].strip()
    lon, lat = coord_str.split(",")
    return category, name, float(lon), float(lat)


# ---------------------------------------------------------------------------
# Geo conversion
# ---------------------------------------------------------------------------


def _lon_to_x(lon: float, zoom: int) -> float:
    return ((lon + 180.0) / 360.0) * (2**zoom)


def _lat_to_y(lat: float, zoom: int) -> float:
    lat_rad = math.radians(lat)
    return (
        (1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi)
        / 2.0
        * (2**zoom)
    )


def geo_to_pixel(lon: float, lat: float, m: StaticMap) -> tuple[int, int]:
    """Convert geographic coordinates to pixel coordinates on the rendered map."""
    zoom = m.zoom
    tile_size = m.tile_size if hasattr(m, "tile_size") else 256
    x = _lon_to_x(lon, zoom)
    y = _lat_to_y(lat, zoom)
    px = int((x - m.x_center) * tile_size + m.width / 2)
    py = int((y - m.y_center) * tile_size + m.height / 2)
    return px, py


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def render_map(
    coords: list[tuple[float, float]],
    stations: list[tuple[str, float, float]],
    pois: list[tuple[str, str, float, float]],
    output_path: str,
    width: int = 900,
    height: int = 600,
) -> None:
    """Render route, stations, POIs, and legend overlay to a PNG map."""
    m = StaticMap(width, height, padding_x=40, padding_y=40)

    # Simplify track for rendering
    simplified = coords[::5] if len(coords) > 100 else coords

    # Add route line
    if simplified:
        line = Line(simplified, "#E63946", 3)
        m.add_line(line)

    # Add invisible POI markers so staticmap includes them in the bounding box
    for category, name, lon, lat in pois:
        marker = CircleMarker((lon, lat), "#ffffff00", 1)
        m.add_marker(marker)

    # Add station markers (larger, on top) — POIs are drawn later as icons
    for i, (name, lon, lat) in enumerate(stations):
        color = "#1D3557"
        marker = CircleMarker((lon, lat), color, 9)
        m.add_marker(marker)
        inner = CircleMarker((lon, lat), "white", 5)
        m.add_marker(inner)

    # Render base map
    image = m.render()
    draw = ImageDraw.Draw(image)

    # Load fonts
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11
        )
        font_bold = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 11
        )
        font_small = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10
        )
    except (OSError, IOError):
        font = ImageFont.load_default()
        font_bold = font
        font_small = font

    # --- POI icons on map ---
    for category, name, lon, lat in pois:
        px, py = geo_to_pixel(lon, lat, m)
        info = POI_CATEGORIES.get(category, {})
        icon_file = ICON_DIR / info.get("icon", "sight.png")
        if icon_file.exists():
            icon = Image.open(icon_file).convert("RGBA")
            icon = icon.resize((ICON_SIZE, ICON_SIZE), Image.LANCZOS)
            # Center icon on coordinate
            ix = px - ICON_SIZE // 2
            iy = py - ICON_SIZE // 2
            # Keep within bounds
            ix = max(0, min(ix, width - ICON_SIZE))
            iy = max(0, min(iy, height - ICON_SIZE))
            image.paste(icon, (ix, iy), mask=icon)

    # --- Station labels on map ---
    for name, lon, lat in stations:
        px, py = geo_to_pixel(lon, lat, m)
        text = name
        bbox = draw.textbbox((0, 0), text, font=font_bold)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        tx = px - tw // 2
        ty = py - th - 15

        # Keep label within map bounds
        tx = max(4, min(tx, width - tw - 4))
        ty = max(4, ty)

        pad = 3
        draw.rectangle(
            [tx - pad, ty - pad, tx + tw + pad, ty + th + pad],
            fill="white",
            outline="#444444",
        )
        draw.text((tx, ty), text, fill="#1D3557", font=font_bold)

    # --- Legend overlay (bottom-left corner) ---
    if pois:
        used_categories = sorted(set(cat for cat, _, _, _ in pois))
        line_height = 18
        legend_h = 30 + (len(used_categories) + 2) * line_height
        legend_w = 175
        lx = 12
        ly = height - legend_h - 12

        # Semi-transparent background
        overlay = Image.new("RGBA", (legend_w, legend_h), (255, 255, 255, 220))
        image.paste(
            Image.alpha_composite(
                Image.new("RGBA", overlay.size, (0, 0, 0, 0)), overlay
            ).convert("RGB"),
            (lx, ly),
            mask=overlay.split()[3],
        )

        # Border
        draw.rectangle(
            [lx, ly, lx + legend_w - 1, ly + legend_h - 1],
            outline="#666666",
        )

        cx = lx + 10
        cy = ly + 10

        draw.text((cx, cy), "Legende", fill="#333333", font=font_bold)
        cy += line_height + 4

        # Station marker
        draw.ellipse([cx, cy + 2, cx + 10, cy + 12], fill="#1D3557")
        draw.ellipse([cx + 2, cy + 4, cx + 8, cy + 10], fill="white")
        draw.text((cx + 16, cy), "Station (Tag)", fill="#333333", font=font_small)
        cy += line_height

        # Route line
        draw.line([(cx, cy + 6), (cx + 10, cy + 6)], fill="#E63946", width=3)
        draw.text((cx + 16, cy), "Route", fill="#333333", font=font_small)
        cy += line_height + 2

        # POI categories
        for cat in used_categories:
            info = POI_CATEGORIES.get(cat, {"color": "#999", "label": cat})
            icon_file = ICON_DIR / info.get("icon", "sight.png")
            if icon_file.exists():
                icon = Image.open(icon_file).convert("RGBA")
                icon = icon.resize((LEGEND_ICON_SIZE, LEGEND_ICON_SIZE), Image.LANCZOS)
                image.paste(icon, (cx, cy + 1), mask=icon)
            else:
                draw.ellipse([cx + 1, cy + 3, cx + 9, cy + 11], fill=info["color"])
            draw.text((cx + LEGEND_ICON_SIZE + 6, cy), info["label"], fill="#333333", font=font_small)
            cy += line_height

    # Save
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, quality=90)
    print(
        f"Map saved to {output_path} "
        f"({Path(output_path).stat().st_size // 1024} KB, "
        f"{len(stations)} stations, {len(pois)} POIs)"
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Render roadtrip map from GPX")
    parser.add_argument("gpx_file", help="Path to GPX file")
    parser.add_argument("output_png", help="Output PNG path")
    parser.add_argument(
        "--stations", nargs="*", default=[],
        help="Station markers as 'Name:lon,lat'",
    )
    parser.add_argument(
        "--pois", nargs="*", default=[],
        help="POI markers as 'category:name:lon,lat' (categories: art, hike, swim, food, wine, sight, nature, coffee)",
    )
    parser.add_argument("--width", type=int, default=900)
    parser.add_argument("--height", type=int, default=600)

    args = parser.parse_args()

    coords = parse_gpx(args.gpx_file)
    stations = [parse_station(s) for s in args.stations]
    pois = [parse_poi(p) for p in args.pois]

    print(f"Loaded {len(coords)} track points from GPX")
    print(f"Rendering map with {len(stations)} stations, {len(pois)} POIs...")

    render_map(coords, stations, pois, args.output_png, args.width, args.height)


if __name__ == "__main__":
    main()
