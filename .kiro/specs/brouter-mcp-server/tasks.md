# Implementation Plan: BRouter MCP Server

## Overview

Build a single-file Python MCP server (`brouter-mcp/server.py`) using FastMCP that wraps the BRouter cycling routing API and Nominatim geocoding API. The server exposes two tools — `calculate_route` and `search_location` — as drop-in replacements for the OpenRouteService MCP routing tools. Implementation proceeds bottom-up: project setup → data models → validation → internal helpers → tool implementations → integration wiring → MCP config.

## Tasks

- [x] 1. Set up project structure and dependencies
  - Create `brouter-mcp/` directory with `pyproject.toml` defining the package metadata, Python >=3.11 requirement, and dependencies: `fastmcp`, `httpx`
  - Add dev dependencies: `pytest`, `hypothesis`, `respx`
  - Create `brouter-mcp/server.py` with the FastMCP entry point: `mcp = FastMCP("BRouter Cycling Router")` and `mcp.run()` in `__main__` block
  - Verify the server starts with `uv run python server.py --help` or similar smoke check
  - _Requirements: 10.1, 10.2, 10.3_

- [x] 2. Implement data models and input validation
  - [x] 2.1 Create data model dataclasses
    - Define `RouteRequest`, `NoGoArea`, `RouteMetadata`, and `GeocodingResult` dataclasses in `server.py`
    - `NoGoArea.radius` defaults to `20.0` meters
    - `RouteRequest` defaults: `profile="trekking"`, `format="gpx"`, `alternativeidx=0`
    - _Requirements: 2.2, 7.3, 8.2, 9.3_

  - [x] 2.2 Implement input validation functions
    - `validate_waypoints(waypoints)` — reject fewer than 2 waypoints
    - `validate_coordinates(lon, lat)` — reject longitude outside [-180, 180] or latitude outside [-90, 90]
    - `validate_profile(profile)` — accept only the 8 valid profiles, reject others with error listing valid options
    - `validate_alternativeidx(idx)` — reject values outside 0–3
    - All validators return descriptive error strings (not exceptions) for MCP tool responses
    - _Requirements: 2.1, 2.4, 5.3, 5.4, 8.3_

  - [x] 2.3 Write property test: coordinate validation (Property 3)
    - **Property 3: Coordinate validation accepts valid ranges and rejects invalid**
    - Generate random float pairs with Hypothesis; verify acceptance iff lon ∈ [-180, 180] and lat ∈ [-90, 90]
    - `@settings(max_examples=100)`
    - **Validates: Requirements 5.4**

  - [x] 2.4 Write property test: profile validation (Property 2)
    - **Property 2: Profile validation accepts exactly the valid set**
    - Generate mix of valid profile names and arbitrary strings; verify acceptance matches the valid set exactly
    - `@settings(max_examples=100)`
    - **Validates: Requirements 2.1, 2.4**

- [x] 3. Implement route request builder and GPX helpers
  - [x] 3.1 Implement `build_brouter_url` function
    - Format waypoints as `lon,lat|lon,lat|...` in the `lonlats` parameter
    - Append `profile`, `format`, `alternativeidx` query parameters
    - Append `nogos=lon,lat,radius|...` only when no-go areas are provided; omit when `None`
    - Base URL: `https://brouter.de/brouter`
    - _Requirements: 1.1, 1.4, 2.3, 7.1, 8.1, 9.1, 9.2_

  - [x] 3.2 Write property test: URL construction (Property 1)
    - **Property 1: URL construction preserves all route parameters**
    - Generate random valid waypoints (2+), profiles, formats, alternative indices, and optional no-go areas; parse the resulting URL and verify all parameters are present and correctly formatted
    - `@settings(max_examples=100)`
    - **Validates: Requirements 1.1, 1.4, 2.3, 7.1, 8.1, 9.1**

  - [x] 3.3 Implement `parse_gpx_metadata` function
    - Extract `track-length` and `filtered ascend` from the GPX creator attribute or comment header using regex
    - Return a `RouteMetadata` dataclass instance
    - _Requirements: 4.1, 4.2_

  - [x] 3.4 Implement `calculate_duration` function
    - Compute duration as `distance / speed` with speeds: 15 km/h (trekking), 20 km/h (fastbike), 12 km/h (all others)
    - Format result as `"Xh Ym"`
    - _Requirements: 4.3_

  - [x] 3.5 Implement `insert_track_name` function
    - Insert or replace `<name>` element inside the `<trk>` element of a GPX string
    - Use `xml.etree.ElementTree` for XML manipulation
    - _Requirements: 3.4_

  - [x] 3.6 Write property test: GPX metadata extraction (Property 5)
    - **Property 5: GPX metadata extraction round-trip**
    - Generate random non-negative numeric values, embed in GPX comment format, verify `parse_gpx_metadata` extracts them correctly
    - `@settings(max_examples=100)`
    - **Validates: Requirements 4.1, 4.2**

  - [x] 3.7 Write property test: duration calculation (Property 6)
    - **Property 6: Duration calculation correctness**
    - Generate random positive distances and valid profiles; verify the formula `distance / speed` with correct speed per profile
    - `@settings(max_examples=100)`
    - **Validates: Requirements 4.3**

  - [x] 3.8 Write property test: track name insertion (Property 4)
    - **Property 4: Track name insertion into GPX**
    - Generate random non-empty track names and valid GPX strings with `<trk>` elements; verify the resulting XML has the correct `<name>` child
    - `@settings(max_examples=100)`
    - **Validates: Requirements 3.4**

- [x] 4. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement HTTP client and Nominatim rate limiter
  - [x] 5.1 Implement `NominatimRateLimiter` class
    - Use `asyncio.Lock` and timestamp tracking to enforce minimum 1 second between requests
    - `async def acquire()` sleeps for remaining time if less than 1 second has elapsed
    - _Requirements: 6.7_

  - [x] 5.2 Implement HTTP client functions
    - `call_brouter(url)` — async GET with 60-second timeout, returns response text or error string
    - `call_nominatim(params)` — async GET with 10-second timeout, `User-Agent: brouter-mcp/1.0 (cycling tour planner)` header, rate-limited via `NominatimRateLimiter`
    - Handle `httpx.TimeoutException` and `httpx.HTTPStatusError` with descriptive error messages
    - _Requirements: 5.1, 5.2, 5.5, 6.1, 6.2_

- [x] 6. Implement MCP tool: `calculate_route`
  - [x] 6.1 Implement the `calculate_route` tool function
    - Register with `@mcp.tool()` decorator
    - Accept parameters: `waypoints`, `profile`, `format`, `alternativeidx`, `nogos`, `track_name`
    - Validate all inputs using validation functions; return error strings on failure
    - Build BRouter URL via `build_brouter_url`
    - Call BRouter API via `call_brouter`
    - For GPX responses: verify `<trk>` element exists, extract metadata, optionally insert track name, format response with route summary + GPX data
    - For GeoJSON responses: return the GeoJSON content directly
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 5.3, 5.4, 5.5, 7.1, 7.2, 7.3, 8.1, 8.2, 8.3, 9.1, 9.2, 9.3, 10.5_

  - [x] 6.2 Write unit tests for `calculate_route` edge cases
    - Test default profile is `trekking`, default format is `gpx`, default alternativeidx is `0`
    - Test round-trip route (identical start/end) includes all intermediate waypoints
    - Test no-go areas omitted from URL when none provided
    - Test GPX response validation detects missing `<trk>` elements
    - _Requirements: 1.5, 2.2, 7.3, 8.2, 9.2_

- [x] 7. Implement MCP tool: `search_location`
  - [x] 7.1 Implement the `search_location` tool function
    - Register with `@mcp.tool()` decorator
    - Accept parameters: `query`, `country_code` (default `"de"`), `limit` (default `5`)
    - Call Nominatim API via `call_nominatim` with rate limiting
    - Transform results to `[longitude, latitude]` coordinate order
    - Format response as structured text with numbered results
    - Return "No locations found" message for empty results
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 10.6_

  - [x] 7.2 Write property test: Nominatim result transformation (Property 7)
    - **Property 7: Nominatim result transformation preserves coordinates as longitude-first**
    - Generate random Nominatim-like response dicts with `name`, `lat`, `lon`, `display_name`; verify `coordinates` is `[lon, lat]` and fields map correctly
    - `@settings(max_examples=100)`
    - **Validates: Requirements 6.3**

  - [x] 7.3 Write unit tests for `search_location` edge cases
    - Test default country code is `de`
    - Test empty Nominatim results return "no locations found" message
    - _Requirements: 6.5, 6.6_

- [x] 8. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Integration tests and MCP configuration
  - [x] 9.1 Write integration tests with respx mocks
    - BRouter API returns GPX → tool returns metadata + GPX content
    - BRouter API returns GeoJSON → tool returns GeoJSON content
    - BRouter API returns HTTP 500 → tool returns error with status code and body
    - BRouter API timeout → tool returns "unavailable" error
    - Nominatim returns results → tool returns formatted locations with `[lon, lat]` order
    - Nominatim returns empty results → tool returns "no locations found"
    - Nominatim rate limiter enforces 1-second spacing
    - HTTP client sends correct `User-Agent` header to Nominatim
    - _Requirements: 1.2, 4.4, 5.1, 5.2, 6.1, 6.2, 6.3, 6.6, 6.7, 7.2_

  - [x] 9.2 Configure MCP server in Kiro IDE
    - Add `brouter` entry to `.kiro/settings/mcp.json` with `command: "uv"` and `args: ["run", "--directory", "brouter-mcp", "python", "server.py"]`
    - _Requirements: 10.3, 10.4, 10.7_

- [x] 10. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- The server is a single-file implementation (`brouter-mcp/server.py`) — all components live in one module
- Python is the implementation language throughout (FastMCP, httpx, dataclasses)
- Property tests use Hypothesis with `@settings(max_examples=100)` per the design
- Integration tests use respx for httpx mocking
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
