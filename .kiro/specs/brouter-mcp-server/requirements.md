# Requirements Document

## Introduction

A Python MCP (Model Context Protocol) server that wraps the BRouter cycling routing engine HTTP API, providing reliable cycling route calculation as a drop-in replacement for the OpenRouteService MCP routing tools. BRouter is specialized for cycling, tolerant with waypoint snapping, follows long-distance cycle routes, and includes elevation awareness. The server uses the public BRouter API at `https://brouter.de/brouter` (no API key required) and is built with FastMCP.

This MCP server addresses reliability issues with the current OpenRouteService-based routing (404 errors on waypoint snapping failures, poor geocoding in rural areas) by leveraging BRouter's more forgiving waypoint handling and cycling-optimized routing profiles. The server also integrates Nominatim geocoding since BRouter has no built-in location search.

## Glossary

- **BRouter_Server**: The Python MCP server application that exposes BRouter routing and Nominatim geocoding as MCP tools
- **BRouter_API**: The public HTTP API at `https://brouter.de/brouter` that performs route calculation
- **Nominatim_API**: The OpenStreetMap Nominatim geocoding API at `https://nominatim.openstreetmap.org` that resolves place names to coordinates
- **MCP_Client**: The Kiro IDE or any MCP-compatible client that invokes tools on the BRouter_Server
- **Waypoint**: A geographic coordinate pair in `[longitude, latitude]` format that defines a point the route must pass through
- **Cycling_Profile**: A BRouter routing profile that determines road preferences and cost functions; available profiles on the public server include `trekking`, `fastbike`, `trekking-ignore-cr`, `safety`, `shortest`, `trekking-steep`, `trekking-noferries`, `trekking-nosteps`
- **GPX**: GPS Exchange Format, an XML schema for geographic data; BRouter returns tracks in `<trk>/<trkseg>/<trkpt>` format with elevation data in `<ele>` elements
- **GeoJSON**: A geographic data format using JSON; an alternative output format from BRouter
- **Round_Trip**: A route where the start and end coordinates are identical, with the route shape defined by intermediate waypoints
- **Track_Metadata**: Summary information extracted from the BRouter GPX comment header, including `track-length` (meters), `filtered ascend` (meters), and `plain-ascend` (meters)
- **No_Go_Area**: A circular area defined by center coordinates and radius that the routing algorithm excludes from the route
- **FastMCP**: A Python framework for building MCP servers with minimal boilerplate

## Requirements

### Requirement 1: Route Calculation

**User Story:** As a tour planner, I want to calculate cycling routes through multiple waypoints via BRouter, so that I get reliable GPX tracks for my tours without the snapping failures of OpenRouteService.

#### Acceptance Criteria

1. WHEN the MCP_Client calls the route calculation tool with a list of Waypoint coordinate pairs, THE BRouter_Server SHALL send an HTTP GET request to the BRouter_API with the waypoints formatted as the `lonlats=lon,lat|lon,lat|...` query parameter
2. WHEN the BRouter_API returns a successful HTTP 200 response, THE BRouter_Server SHALL return the GPX data as a string to the MCP_Client
3. THE BRouter_Server SHALL accept a minimum of 2 Waypoint coordinate pairs for a single route calculation
4. WHEN the MCP_Client provides Waypoint coordinates as `[longitude, latitude]` pairs, THE BRouter_Server SHALL preserve the longitude-first coordinate convention when formatting the BRouter_API request
5. WHEN the MCP_Client specifies start and end coordinates that are identical (Round_Trip), THE BRouter_Server SHALL include all intermediate Waypoint coordinates in the BRouter_API request to define the route shape

### Requirement 2: Cycling Profile Selection

**User Story:** As a tour planner, I want to choose between different cycling profiles, so that routes match my riding style and terrain preferences.

#### Acceptance Criteria

1. THE BRouter_Server SHALL support the following Cycling_Profile values: `trekking`, `fastbike`, `trekking-ignore-cr`, `safety`, `shortest`, `trekking-steep`, `trekking-noferries`, `trekking-nosteps`
2. WHEN the MCP_Client does not specify a Cycling_Profile, THE BRouter_Server SHALL use `trekking` as the default profile
3. WHEN the MCP_Client specifies a Cycling_Profile, THE BRouter_Server SHALL pass the profile name as the `profile` query parameter to the BRouter_API
4. IF the MCP_Client specifies a Cycling_Profile value that is not in the supported list, THEN THE BRouter_Server SHALL return an error message listing the valid profile options

### Requirement 3: GPX Output Format

**User Story:** As a tour planner, I want GPX output in track format with elevation data, so that I can import routes directly into GPS devices and cycling apps.

#### Acceptance Criteria

1. THE BRouter_Server SHALL request GPX format from the BRouter_API by setting the `format=gpx` query parameter
2. WHEN the BRouter_API returns GPX data, THE BRouter_Server SHALL verify the GPX contains `<trk>/<trkseg>/<trkpt>` elements
3. WHEN the BRouter_API returns GPX data with `<ele>` elements inside `<trkpt>` elements, THE BRouter_Server SHALL preserve the elevation data in the returned GPX
4. WHEN the MCP_Client provides a track name, THE BRouter_Server SHALL include the name in the GPX `<name>` element within the `<trk>` element

### Requirement 4: Route Metadata Extraction

**User Story:** As a tour planner, I want to see route distance, elevation gain, and estimated duration alongside the GPX data, so that I can evaluate the tour difficulty without opening the GPX file.

#### Acceptance Criteria

1. WHEN the BRouter_API returns a successful response, THE BRouter_Server SHALL extract the `track-length` value from the GPX comment header and return it as distance in meters
2. WHEN the BRouter_API returns a successful response, THE BRouter_Server SHALL extract the `filtered ascend` value from the GPX comment header and return it as elevation gain in meters
3. THE BRouter_Server SHALL calculate an estimated cycling duration from the track-length using an average speed of 15 km/h for the `trekking` profile, 20 km/h for the `fastbike` profile, and 12 km/h for all other Cycling_Profile values
4. THE BRouter_Server SHALL return the Track_Metadata (distance, elevation gain, estimated duration) as structured text alongside the GPX content in the tool response

### Requirement 5: Error Handling

**User Story:** As a tour planner, I want clear error messages when routing fails, so that I can adjust waypoints or parameters and retry.

#### Acceptance Criteria

1. IF the BRouter_API returns an HTTP error status code, THEN THE BRouter_Server SHALL return a descriptive error message that includes the HTTP status code and the response body text from the BRouter_API
2. IF the BRouter_API is unreachable due to a connection timeout or network error, THEN THE BRouter_Server SHALL return an error message stating that the BRouter_API at `brouter.de` is unavailable
3. IF the MCP_Client provides fewer than 2 Waypoint coordinate pairs, THEN THE BRouter_Server SHALL return an error message stating that at least 2 waypoints are required
4. IF the MCP_Client provides Waypoint coordinates with latitude outside the range -90 to 90 or longitude outside the range -180 to 180, THEN THE BRouter_Server SHALL return an error message identifying the invalid coordinates
5. THE BRouter_Server SHALL set a request timeout of 60 seconds for all BRouter_API HTTP calls

### Requirement 6: Geocoding via Nominatim

**User Story:** As a tour planner, I want to search for locations by name and get coordinates, so that I can find waypoints without manually looking up coordinates.

#### Acceptance Criteria

1. WHEN the MCP_Client calls the geocoding tool with a search query string, THE BRouter_Server SHALL send an HTTP GET request to the Nominatim_API search endpoint with the query as the `q` parameter
2. THE BRouter_Server SHALL include a `User-Agent` header identifying the application in all Nominatim_API requests, as required by the Nominatim usage policy
3. WHEN the Nominatim_API returns results, THE BRouter_Server SHALL return each result with the place name, coordinates as `[longitude, latitude]`, and the display address
4. WHEN the MCP_Client provides a `country_code` parameter, THE BRouter_Server SHALL pass it as the `countrycodes` parameter to the Nominatim_API to restrict results to that country
5. THE BRouter_Server SHALL default the `countrycodes` parameter to `de` (Germany) when the MCP_Client does not provide a country code
6. WHEN the Nominatim_API returns zero results, THE BRouter_Server SHALL return a message stating that no locations were found for the given query
7. THE BRouter_Server SHALL limit Nominatim_API requests to a maximum of 1 request per second to comply with the Nominatim usage policy

### Requirement 7: GeoJSON Output Support

**User Story:** As a tour planner, I want to optionally receive route data as GeoJSON, so that I can use it for programmatic processing and map rendering.

#### Acceptance Criteria

1. WHEN the MCP_Client requests GeoJSON format, THE BRouter_Server SHALL set the `format=geojson` query parameter in the BRouter_API request
2. WHEN the BRouter_API returns GeoJSON data, THE BRouter_Server SHALL return the GeoJSON string to the MCP_Client
3. WHEN the MCP_Client does not specify an output format, THE BRouter_Server SHALL default to GPX format

### Requirement 8: Alternative Route Selection

**User Story:** As a tour planner, I want to request alternative routes for the same waypoints, so that I can compare different route options.

#### Acceptance Criteria

1. WHEN the MCP_Client specifies an alternative route index with a value of 0, 1, 2, or 3, THE BRouter_Server SHALL pass the value as the `alternativeidx` query parameter to the BRouter_API
2. WHEN the MCP_Client does not specify an alternative route index, THE BRouter_Server SHALL default to index 0 (primary route)
3. IF the MCP_Client specifies an alternative route index outside the range 0 to 3, THEN THE BRouter_Server SHALL return an error message stating that the valid range is 0 to 3

### Requirement 9: No-Go Area Support

**User Story:** As a tour planner, I want to define areas the route should avoid, so that I can steer routes away from construction zones, busy roads, or other obstacles.

#### Acceptance Criteria

1. WHEN the MCP_Client provides a list of No_Go_Area definitions (each containing longitude, latitude, and radius in meters), THE BRouter_Server SHALL format them as the `nogos=lon,lat,radius|lon,lat,radius|...` query parameter in the BRouter_API request
2. WHEN the MCP_Client does not provide No_Go_Area definitions, THE BRouter_Server SHALL omit the `nogos` parameter from the BRouter_API request
3. THE BRouter_Server SHALL use a default radius of 20 meters for a No_Go_Area when the MCP_Client does not specify a radius

### Requirement 10: MCP Server Packaging and Integration

**User Story:** As a developer, I want the BRouter MCP server to be installable and configurable in the Kiro IDE, so that I can use it alongside existing MCP servers.

#### Acceptance Criteria

1. THE BRouter_Server SHALL be implemented as a Python package in the `brouter-mcp/` directory at the workspace root
2. THE BRouter_Server SHALL use the FastMCP framework to expose tools via the MCP protocol
3. THE BRouter_Server SHALL be runnable via `uvx` or `uv run` from the `brouter-mcp/` directory
4. THE BRouter_Server SHALL be configurable in `.kiro/settings/mcp.json` using the standard MCP server format with `command` and `args` fields
5. THE BRouter_Server SHALL expose a tool named `calculate_route` for cycling route calculation
6. THE BRouter_Server SHALL expose a tool named `search_location` for Nominatim geocoding
7. THE BRouter_Server SHALL start and respond to MCP tool calls without requiring any API keys or authentication credentials
