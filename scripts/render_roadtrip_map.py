#!/usr/bin/env python3
"""Render a roadtrip route map as PNG using staticmap.

Usage:
    python scripts/render_roadtrip_map.py <gpx_file> <output_png> [--stations 'Name:lon,lat' ...]

Example:
    python scripts/render_roadtrip_map.py \
        roadtrips/gpx/nordspanien-kueste.gpx \
        roadtrips/img/nordspanien-kueste.png \
        --stations 'Bilbao:-2.9253,43.2627' 'San Sebastián:-1.9812,43.3183' \
                   'Santander:-3.8044,43.4623' 'Cangas de Onís:-5.0847,43.3499' \
                   'Gijón:-5.6611,43.5322'
"""

import argparse
import math
import xml.etree.ElementTree as ET
from pathlib import Path

from staticmap import StaticMap, Line, CircleMarker
from PIL import Image, ImageDraw, ImageFont


def parse_gpx(gpx_path: str) -> list[tuple[float, float]]:
    """Parse GPX file and return list of (lon, lat) coordinates."""
    tree = ET.parse(gpx_path)
    root = tree.getroot()

    # Handle GPX namespace
    ns = {"gpx": "http://www.topografix.com/GPX/1/1"}

    coords = []
    # Try tracks first
    for trkpt in root.findall(".//gpx:trkpt", ns):
        lat = float(trkpt.get("lat"))
        lon = float(trkpt.get("lon"))
        coords.append((lon, lat))

    # Fall back to route points
    if not coords:
        for rtept in root.findall(".//gpx:rtept", ns):
            lat = float(rtept.get("lat"))
            lon = float(rtept.get("lon"))
            coords.append((lon, lat))

    return coords


def parse_station(station_str: str) -> tuple[str, float, float]:
    """Parse 'Name:lon,lat' string."""
    name, coords = station_str.rsplit(":", 1)
    lon, lat = coords.split(",")
    return name.strip(), float(lon), float(lat)


def _lon_to_x(lon: float, zoom: int) -> float:
    """Convert longitude to tile x coordinate."""
    return ((lon + 180.0) / 360.0) * (2**zoom)


def _lat_to_y(lat: float, zoom: int) -> float:
    """Convert latitude to tile y coordinate."""
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


def render_map(
    coords: list[tuple[float, float]],
    stations: list[tuple[str, float, float]],
    output_path: str,
    width: int = 800,
    height: int = 600,
) -> None:
    """Render route and stations to a PNG map."""
    m = StaticMap(width, height, padding_x=40, padding_y=40)

    # Simplify track for rendering (every 5th point)
    simplified = coords[::5] if len(coords) > 100 else coords

    # Add route line
    if simplified:
        line = Line(simplified, "#E63946", 3)
        m.add_line(line)

    # Add station markers — first station blue, rest red
    for i, (name, lon, lat) in enumerate(stations):
        color = "#1D3557" if i == 0 else "#E63946"
        marker = CircleMarker((lon, lat), color, 8)
        m.add_marker(marker)
        inner = CircleMarker((lon, lat), "white", 4)
        m.add_marker(inner)

    # Render base map
    image = m.render()

    # Add station labels
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12
        )
    except (OSError, IOError):
        font = ImageFont.load_default()

    for name, lon, lat in stations:
        px, py = geo_to_pixel(lon, lat, m)

        text = name
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        # Position label above marker
        tx = px - tw // 2
        ty = py - th - 14

        # Background rectangle
        pad = 3
        draw.rectangle(
            [tx - pad, ty - pad, tx + tw + pad, ty + th + pad],
            fill="white",
            outline="#666666",
        )
        draw.text((tx, ty), text, fill="#333333", font=font)

    # Save
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)
    print(f"Map saved to {output_path} ({Path(output_path).stat().st_size // 1024} KB)")


def main():
    parser = argparse.ArgumentParser(description="Render roadtrip map from GPX")
    parser.add_argument("gpx_file", help="Path to GPX file")
    parser.add_argument("output_png", help="Output PNG path")
    parser.add_argument(
        "--stations",
        nargs="*",
        default=[],
        help="Station markers as 'Name:lon,lat'",
    )
    parser.add_argument("--width", type=int, default=800)
    parser.add_argument("--height", type=int, default=600)

    args = parser.parse_args()

    coords = parse_gpx(args.gpx_file)
    stations = [parse_station(s) for s in args.stations]

    print(f"Loaded {len(coords)} track points from GPX")
    print(f"Rendering map with {len(stations)} stations...")

    render_map(coords, stations, args.output_png, args.width, args.height)


if __name__ == "__main__":
    main()
