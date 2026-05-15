"""MCP server wrapping the public OSRM API for car routing with GPX export.

Uses lib.routing for all API logic. This file only provides MCP tool
declarations and formats structured results into human-readable strings.

Usage:
    fastmcp run server.py
"""

from fastmcp import FastMCP

from lib.routing import calculate_car_route as _calculate, route_to_gpx as _route_to_gpx

mcp = FastMCP("OSRM Car Routing")


@mcp.tool()
async def calculate_car_route(
    waypoints: list[list[float]],
    overview: str = "full",
) -> str:
    """Calculate a car route between waypoints via OSRM.

    Returns distance, duration, and per-leg breakdown.
    No API key required (public OSRM demo server, OSM data).

    Args:
        waypoints: List of [longitude, latitude] coordinate pairs (min 2, max 100).
        overview: Geometry detail — "full" (default), "simplified", or "false".
    """
    if len(waypoints) > 100:
        return "Error: Maximum 100 waypoints supported."

    result = await _calculate(waypoints, overview=overview)

    if "error" in result:
        return f"Error: {result['error']}"

    hours = int(result["duration_min"] // 60)
    minutes = int(result["duration_min"] % 60)

    lines = [
        "## Route Summary (car)",
        "",
        f"- **Total distance:** {result['distance_km']:.1f} km",
        f"- **Total duration:** {hours}h {minutes:02d}min",
        f"- **Waypoints:** {len(waypoints)}",
    ]

    return "\n".join(lines)


@mcp.tool()
async def route_to_gpx(
    waypoints: list[list[float]],
    output_path: str,
    track_name: str = "route",
    station_names: list[str] | None = None,
) -> str:
    """Calculate a car route and save it as a GPX file.

    The GPX contains the full road geometry as a track, plus optional
    named waypoints for the stations.

    Args:
        waypoints: List of [longitude, latitude] coordinate pairs (min 2).
        output_path: Absolute path where the GPX file will be saved.
        track_name: Name for the GPX track element.
        station_names: Optional list of station names (same length as waypoints).
    """
    result = await _route_to_gpx(waypoints, output_path, track_name, station_names)

    if "error" in result:
        return f"Error: {result['error']}"

    hours = int(result["duration_min"] // 60)
    minutes = int(result["duration_min"] % 60)

    return (
        f"GPX saved to {result['path']}\n"
        f"- Track points: {result['track_points']}\n"
        f"- Distance: {result['distance_km']:.1f} km\n"
        f"- Duration: {hours}h {minutes:02d}min\n"
        f"- Waypoints: {result['waypoint_count']}"
    )


if __name__ == "__main__":
    mcp.run()
