"""Tests for the render_elevation_profile MCP tool."""

import asyncio
import os
import tempfile

from server import render_elevation_profile


def _make_gpx_with_elevation(points: list[tuple[float, float, float]]) -> str:
    """Build a GPX string from (lon, lat, ele) triples."""
    pts = "\n".join(
        f'    <trkpt lat="{lat}" lon="{lon}"><ele>{ele}</ele></trkpt>'
        for lon, lat, ele in points
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">\n'
        f"  <trk><name>Test</name><trkseg>\n{pts}\n  </trkseg></trk>\n"
        "</gpx>"
    )


def _write_gpx(tmp_dir: str, content: str) -> str:
    gpx_path = os.path.join(tmp_dir, "test.gpx")
    with open(gpx_path, "w", encoding="utf-8") as f:
        f.write(content)
    return gpx_path


def test_file_not_found() -> None:
    result = asyncio.run(render_elevation_profile(
        gpx_path="/nonexistent/path.gpx",
        output_path="/tmp/out.png",
    ))
    assert "not found" in result.lower()


def test_too_few_elevation_points() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        gpx = _make_gpx_with_elevation([(13.4, 52.5, 35.0)])
        gpx_path = _write_gpx(tmp_dir, gpx)
        result = asyncio.run(render_elevation_profile(
            gpx_path=gpx_path,
            output_path=os.path.join(tmp_dir, "out.png"),
        ))
        assert "fewer than 2" in result.lower()

def test_creates_png() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        gpx = _make_gpx_with_elevation([
            (13.0, 52.5, 30.0),
            (13.01, 52.5, 35.0),
            (13.02, 52.5, 50.0),
            (13.03, 52.5, 40.0),
            (13.04, 52.5, 32.0),
        ])
        gpx_path = _write_gpx(tmp_dir, gpx)
        output_path = os.path.join(tmp_dir, "profile.png")

        result = asyncio.run(render_elevation_profile(
            gpx_path=gpx_path,
            output_path=output_path,
        ))

        assert "rendered" in result.lower()
        assert os.path.isfile(output_path)
        with open(output_path, "rb") as f:
            assert f.read(4) == b"\x89PNG"


def test_reports_stats() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        gpx = _make_gpx_with_elevation([
            (13.0, 52.5, 30.0),
            (13.01, 52.5, 50.0),
            (13.02, 52.5, 40.0),
        ])
        gpx_path = _write_gpx(tmp_dir, gpx)
        output_path = os.path.join(tmp_dir, "profile.png")

        result = asyncio.run(render_elevation_profile(
            gpx_path=gpx_path,
            output_path=output_path,
        ))

        assert "30–50 m" in result
        assert "↑20 m" in result
        assert "↓10 m" in result


def test_creates_output_directory() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        gpx = _make_gpx_with_elevation([
            (13.0, 52.5, 30.0),
            (13.01, 52.5, 35.0),
        ])
        gpx_path = _write_gpx(tmp_dir, gpx)
        output_path = os.path.join(tmp_dir, "sub", "dir", "profile.png")

        result = asyncio.run(render_elevation_profile(
            gpx_path=gpx_path,
            output_path=output_path,
        ))

        assert "rendered" in result.lower()
        assert os.path.isfile(output_path)
