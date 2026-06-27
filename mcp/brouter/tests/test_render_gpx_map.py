"""Tests for the render_gpx_map MCP tool."""

import asyncio
import os
import tempfile

from server import render_gpx_map

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_gpx(trackpoints: list[tuple[float, float]]) -> str:
    """Build a minimal GPX string from (lon, lat) pairs."""
    pts = "\n".join(
        f'    <trkpt lat="{lat}" lon="{lon}"><ele>35</ele></trkpt>' for lon, lat in trackpoints
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">\n'
        f"  <trk><name>Test</name><trkseg>\n{pts}\n  </trkseg></trk>\n"
        "</gpx>"
    )


def _write_gpx(tmp_dir: str, content: str) -> str:
    """Write GPX content to a temp file and return the path."""
    gpx_path = os.path.join(tmp_dir, "test.gpx")
    with open(gpx_path, "w", encoding="utf-8") as f:
        f.write(content)
    return gpx_path


# ---------------------------------------------------------------------------
# Tests: error handling
# ---------------------------------------------------------------------------


def test_render_gpx_map_file_not_found() -> None:
    """Returns error when GPX file does not exist."""
    result = asyncio.run(
        render_gpx_map(
            gpx_path="/nonexistent/path.gpx",
            output_path="/tmp/out.png",
        )
    )
    assert "not found" in result.lower()


def test_render_gpx_map_invalid_gpx() -> None:
    """Returns error when file is not valid GPX."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        gpx_path = os.path.join(tmp_dir, "bad.gpx")
        with open(gpx_path, "w") as f:
            f.write("this is not xml")

        result = asyncio.run(
            render_gpx_map(
                gpx_path=gpx_path,
                output_path=os.path.join(tmp_dir, "out.png"),
            )
        )
        assert "error" in result.lower()


def test_render_gpx_map_too_few_trackpoints() -> None:
    """Returns error when GPX has fewer than 2 trackpoints."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        gpx_content = _make_gpx([(13.4, 52.5)])
        gpx_path = _write_gpx(tmp_dir, gpx_content)

        result = asyncio.run(
            render_gpx_map(
                gpx_path=gpx_path,
                output_path=os.path.join(tmp_dir, "out.png"),
            )
        )
        assert "fewer than 2" in result.lower()


# ---------------------------------------------------------------------------
# Tests: successful rendering
# ---------------------------------------------------------------------------


def test_render_gpx_map_creates_png() -> None:
    """Successfully renders a GPX track to a PNG file."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        gpx_content = _make_gpx(
            [
                (13.0672, 52.3918),
                (13.05, 52.395),
                (13.04, 52.39),
                (13.0672, 52.3918),
            ]
        )
        gpx_path = _write_gpx(tmp_dir, gpx_content)
        output_path = os.path.join(tmp_dir, "route.png")

        result = asyncio.run(
            render_gpx_map(
                gpx_path=gpx_path,
                output_path=output_path,
            )
        )

        assert "successfully" in result.lower()
        assert os.path.isfile(output_path)
        # PNG files start with the PNG magic bytes
        with open(output_path, "rb") as f:
            header = f.read(8)
        assert header[:4] == b"\x89PNG"


def test_render_gpx_map_creates_output_directory() -> None:
    """Creates the output directory if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        gpx_content = _make_gpx(
            [
                (13.4, 52.52),
                (13.45, 52.51),
            ]
        )
        gpx_path = _write_gpx(tmp_dir, gpx_content)
        output_path = os.path.join(tmp_dir, "subdir", "nested", "route.png")

        result = asyncio.run(
            render_gpx_map(
                gpx_path=gpx_path,
                output_path=output_path,
            )
        )

        assert "successfully" in result.lower()
        assert os.path.isfile(output_path)


def test_render_gpx_map_custom_dimensions() -> None:
    """Respects custom width and height parameters."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        gpx_content = _make_gpx(
            [
                (13.4, 52.52),
                (13.45, 52.51),
            ]
        )
        gpx_path = _write_gpx(tmp_dir, gpx_content)
        output_path = os.path.join(tmp_dir, "route.png")

        result = asyncio.run(
            render_gpx_map(
                gpx_path=gpx_path,
                output_path=output_path,
                width=1024,
                height=768,
            )
        )

        assert "1024x768" in result
        assert os.path.isfile(output_path)


def test_render_gpx_map_reports_trackpoint_count() -> None:
    """Result message includes the number of trackpoints."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        gpx_content = _make_gpx(
            [
                (13.0, 52.5),
                (13.1, 52.5),
                (13.2, 52.5),
                (13.3, 52.5),
                (13.4, 52.5),
            ]
        )
        gpx_path = _write_gpx(tmp_dir, gpx_content)
        output_path = os.path.join(tmp_dir, "route.png")

        result = asyncio.run(
            render_gpx_map(
                gpx_path=gpx_path,
                output_path=output_path,
            )
        )

        assert "5 trackpoints" in result
