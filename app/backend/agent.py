"""Gemini agent loop with tool calling and streaming."""

import asyncio
import json
import logging
import re
from collections.abc import AsyncGenerator
from typing import Any

from google import genai
from google.genai import types
from google.genai.errors import ClientError, ServerError
from i18n import Lang
from i18n import msg as i18n_msg
from mcp_manager import MCPManager
from steering import build_system_prompt

logger = logging.getLogger(__name__)

type SSEEvent = dict[str, Any]

# Geo-relevant tool detection by name pattern
GEO_ROUTE_PATTERNS = ("route", "calculate_car", "calculate_bike")
GEO_POINT_PATTERNS = ("geocode", "search_location")
GEO_POI_PATTERNS = ("search_pois",)


def _is_route_tool(name: str) -> bool:
    """Check if a tool name indicates route geometry in the response."""
    return any(p in name for p in GEO_ROUTE_PATTERNS)


def _is_geocode_tool(name: str) -> bool:
    """Check if a tool name indicates geocoding results."""
    return any(p in name for p in GEO_POINT_PATTERNS)


def _is_poi_tool(name: str) -> bool:
    """Check if a tool name indicates POI search results."""
    return any(p in name for p in GEO_POI_PATTERNS)


# Tool name → status message i18n key mapping
_TOOL_STATUS_CATEGORY: dict[str, str] = {
    # Routing
    "mcp_brouter_calculate_route": "status_routing",
    "mcp_osrm_calculate_car_route": "status_routing",
    "mcp_osrm_route_to_gpx": "status_routing",
    "mcp_openrouteservice_calculate_route": "status_routing",
    "mcp_openrouteservice_driving_time": "status_routing",
    "mcp_openrouteservice_isochrone": "status_routing",
    "mcp_openrouteservice_distance_matrix": "status_routing",
    # Location search
    "mcp_brouter_search_location": "status_location",
    "mcp_openrouteservice_geocode": "status_location",
    "mcp_open_meteo_geocoding": "status_location",
    # Weather
    "mcp_open_meteo_weather_forecast": "status_weather",
    # Public transport
    "mcp_vbb_search_stops": "status_transit",
    "mcp_vbb_get_departures": "status_transit",
    "mcp_vbb_get_journeys": "status_transit",
    # POIs
    "mcp_overpass_search_pois_along_route": "status_pois",
    # Trails
    "mcp_waymarkedtrails_search_routes": "status_trails",
    "mcp_waymarkedtrails_get_route_details": "status_trails",
    "mcp_waymarkedtrails_search_routes_in_region": "status_trails",
    "mcp_waymarkedtrails_get_route_segments": "status_trails",
    # Travel info
    "mcp_wikivoyage_search_destinations": "status_travel_info",
    "mcp_wikivoyage_get_article": "status_travel_info",
    "mcp_wikivoyage_get_section": "status_travel_info",
    "mcp_wikivoyage_get_article_sections": "status_travel_info",
    "mcp_wikivoyage_search_nearby": "status_travel_info",
    # Web search
    "mcp_tavily_web_search": "status_web_search",
    "mcp_tavily_web_extract": "status_web_search",
    # Rendering
    "mcp_brouter_render_gpx_map": "status_rendering",
    "mcp_brouter_render_elevation_profile": "status_rendering",
}


def _get_status_categories(tool_names: list[str]) -> list[str]:
    """Deduplicate tool calls into unique status category keys."""
    seen: set[str] = set()
    categories: list[str] = []
    for name in tool_names:
        cat = _TOOL_STATUS_CATEGORY.get(name, "status_generic")
        if cat not in seen:
            seen.add(cat)
            categories.append(cat)
    return categories


def create_client(api_key: str) -> genai.Client:
    """Create a Gemini client."""
    return genai.Client(api_key=api_key)


async def _call_gemini_with_retry(
    client: genai.Client,
    contents: list[types.Content],
    config: types.GenerateContentConfig,
    max_retries: int = 3,
    timeout: float = 180.0,
) -> Any:
    """Call Gemini with exponential backoff on 503/429 errors and a timeout."""
    for attempt in range(max_retries):
        try:
            # generate_content is synchronous — run in thread to avoid blocking event loop
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    client.models.generate_content,
                    model="gemini-2.5-flash",
                    contents=contents,
                    config=config,
                ),
                timeout=timeout,
            )
            return response
        except TimeoutError:
            if attempt < max_retries - 1:
                wait = 2 ** (attempt + 1)
                logger.warning(
                    "Gemini timed out after %.0fs, retrying in %ds (attempt %d/%d)",
                    timeout,
                    wait,
                    attempt + 1,
                    max_retries,
                )
                await asyncio.sleep(wait)
            else:
                raise TimeoutError(
                    f"Gemini did not respond within {timeout}s after {max_retries} attempts"
                )
        except ServerError as e:
            if attempt < max_retries - 1 and e.code in (503, 500):
                wait = 2 ** (attempt + 1)  # 2s, 4s, 8s
                logger.warning(
                    "Gemini %d, retrying in %ds (attempt %d/%d)",
                    e.code,
                    wait,
                    attempt + 1,
                    max_retries,
                )
                await asyncio.sleep(wait)
            else:
                raise
        except ClientError as e:
            if attempt < max_retries - 1 and e.code == 429:
                wait = min(2 ** (attempt + 2), 30)  # 4s, 8s, 16s
                logger.warning(
                    "Gemini 429, retrying in %ds (attempt %d/%d)", wait, attempt + 1, max_retries
                )
                await asyncio.sleep(wait)
            else:
                raise


async def run_agent(
    client: genai.Client,
    user_message: str,
    chat_history: list[dict[str, str]],
    mcp: MCPManager,
    language: str = "de",
) -> AsyncGenerator[SSEEvent, None]:
    """Run the agent loop, yielding SSE events.

    Yields dicts with keys: {"event": str, "data": dict}
    """
    mcp_declarations = await mcp.get_tool_declarations()
    tool_names = [d["name"] for d in mcp_declarations]
    system_prompt: str = build_system_prompt(
        tool_names, language=language, user_message=user_message
    )

    # Use provided language for error messages
    lang: Lang = language if language in ("de", "en") else "de"

    logger.info("Agent started: lang=%s, history=%d messages", lang, len(chat_history))
    logger.debug("System prompt length: %d chars", len(system_prompt))

    # Build conversation contents
    contents: list[types.Content] = []
    for msg in chat_history:
        contents.append(
            types.Content(
                role=msg["role"],
                parts=[types.Part.from_text(text=msg["content"])],
            )
        )
    contents.append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_message)],
        )
    )

    # Configure tools — all declarations come from MCP servers
    tools = types.Tool(
        function_declarations=[types.FunctionDeclaration(**decl) for decl in mcp_declarations]
    )

    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        tools=[tools],
        tool_config=types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(mode="AUTO")
        ),
        temperature=0.7,
        thinking_config=types.ThinkingConfig(thinking_budget=2000),
    )

    # Agent loop: call LLM, execute tools, feed results back
    max_iterations: int = 25
    recovery_count: int = 0  # Track recovery nudges to prevent infinite loops
    max_recoveries: int = 2
    for iteration in range(max_iterations):
        logger.info("Iteration %d: calling Gemini", iteration + 1)
        try:
            response = await _call_gemini_with_retry(client, contents, config)
        except ClientError as e:
            logger.error("Gemini ClientError %d: %s", e.code, e.message)
            if e.code == 429:
                yield {
                    "event": "error",
                    "data": {"error": i18n_msg("quota_exhausted", lang)},
                }
            else:
                yield {
                    "event": "error",
                    "data": {
                        "error": i18n_msg(
                            "api_error", lang, code=str(e.code), detail=e.message or str(e)
                        )
                    },
                }
            return
        except ServerError as e:
            logger.error("Gemini ServerError %d: %s", e.code, e.message)
            yield {
                "event": "error",
                "data": {"error": i18n_msg("server_unavailable", lang, code=str(e.code))},
            }
            return
        except TimeoutError as e:
            logger.error("Gemini request timed out: %s", e)
            yield {
                "event": "error",
                "data": {"error": i18n_msg("server_unavailable", lang, code="timeout")},
            }
            return
        except Exception as e:
            logger.exception("Unexpected error in agent loop")
            yield {
                "event": "error",
                "data": {"error": i18n_msg("unexpected_error", lang, detail=str(e))},
            }
            return

        # Check if response has function calls
        if not response.candidates:
            logger.warning("Gemini returned no candidates at iteration %d", iteration + 1)
            yield {"event": "tour", "data": {"markdown": ""}}
            yield {"event": "done", "data": {"iterations": iteration + 1}}
            return

        candidate = response.candidates[0]
        if not candidate.content or not candidate.content.parts:
            finish_reason = getattr(candidate, "finish_reason", None)
            logger.warning(
                "Gemini returned empty content at iteration %d, finish_reason=%s",
                iteration + 1,
                finish_reason,
            )
            # Log conversation state for debugging
            logger.debug(
                "Conversation has %d messages, last role: %s",
                len(contents),
                contents[-1].role if contents else "none",
            )
            # If blocked by safety, inform user
            if finish_reason and "SAFETY" in str(finish_reason):
                yield {
                    "event": "error",
                    "data": {
                        "error": i18n_msg(
                            "unexpected_error", lang, detail="Response blocked by safety filter"
                        )
                    },
                }
                yield {"event": "done", "data": {"iterations": iteration + 1}}
                return

            # MALFORMED_FUNCTION_CALL: nudge the model to respond with text instead
            if (
                finish_reason
                and "MALFORMED" in str(finish_reason)
                and recovery_count < max_recoveries
            ):
                recovery_count += 1
                logger.info(
                    "Recovering from MALFORMED_FUNCTION_CALL, nudging model (recovery %d)",
                    recovery_count,
                )
                contents.append(
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(
                                text="Your last function call was malformed. Do NOT call any more tools. "
                                "Respond directly with your best answer using the information you already have."
                            )
                        ],
                    )
                )
                continue

            # STOP with empty content: model got confused. Nudge it to produce output.
            if (
                finish_reason
                and "STOP" in str(finish_reason)
                and iteration > 0
                and recovery_count < max_recoveries
            ):
                recovery_count += 1
                logger.info(
                    "Recovering from empty STOP response, nudging model (recovery %d)",
                    recovery_count,
                )
                contents.append(
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(
                                text="Please provide your complete response now based on all the information gathered so far."
                            )
                        ],
                    )
                )
                continue

            yield {"event": "tour", "data": {"markdown": ""}}
            yield {"event": "done", "data": {"iterations": iteration + 1}}
            return

        parts = candidate.content.parts

        function_calls = [p for p in parts if p.function_call]

        if not function_calls:
            # No more tool calls — this is the final response
            text_parts: list[str] = [p.text for p in parts if p.text]
            final_text: str = "\n".join(text_parts)

            # Extract route name from first heading for the log
            heading_match = re.search(r"^#{1,3}\s+(.+)$", final_text, re.MULTILINE)
            route_name = heading_match.group(1).strip() if heading_match else "unnamed"

            logger.info(
                "Agent done: %d iterations, response %d chars", iteration + 1, len(final_text)
            )
            logger.info("✅ Tour generation complete: %s", route_name)
            logger.debug("First 500 chars of response: %s", repr(final_text[:500]))
            yield {"event": "tour", "data": {"markdown": final_text}}
            yield {"event": "done", "data": {"iterations": iteration + 1}}
            return

        # Execute tool calls
        logger.info("Iteration %d: %d tool call(s)", iteration + 1, len(function_calls))
        contents.append(candidate.content)
        tool_results: list[types.Part] = []

        # Emit grouped status messages (one per category, not per tool call)
        call_names = [part.function_call.name for part in function_calls]
        for category_key in _get_status_categories(call_names):
            yield {
                "event": "status",
                "data": {"message": i18n_msg(category_key, lang)},
            }

        for part in function_calls:
            fc = part.function_call
            tool_name: str = fc.name
            tool_args: dict[str, Any] = dict(fc.args) if fc.args else {}

            logger.info(
                "Tool call: %s(%s)", tool_name, json.dumps(tool_args, ensure_ascii=False)[:150]
            )

            # Extract POI coordinates from render_gpx_map arguments
            if tool_name == "mcp_brouter_render_gpx_map" and tool_args.get("pois"):
                pois_arg = tool_args["pois"]
                poi_list: list[dict[str, Any]] = []
                for poi in pois_arg:
                    lat_p = poi.get("lat")
                    lon_p = poi.get("lon")
                    if lat_p is not None and lon_p is not None:
                        poi_list.append(
                            {
                                "lat": lat_p,
                                "lon": lon_p,
                                "name": poi.get("name", ""),
                                "category": poi.get("category", ""),
                            }
                        )
                if poi_list:
                    logger.info("Emitting %d POI markers from render_gpx_map args", len(poi_list))
                    yield {
                        "event": "map",
                        "data": {"pois": poi_list},
                    }

            # Execute the tool via MCP
            result_str: str
            try:
                result: Any = await mcp.call_tool(tool_name, tool_args)

                # Emit geo events based on name patterns
                if isinstance(result, dict):
                    if _is_route_tool(tool_name):
                        geometry = result.get("geometry")
                        if geometry:
                            yield {
                                "event": "map",
                                "data": {"route": [[lat, lon] for lat, lon in geometry]},
                            }
                        # Auto-save GPX to temp file so subsequent tools can use it
                        gpx_content = result.get("gpx")
                        if gpx_content:
                            import math
                            import os
                            import tempfile
                            import xml.etree.ElementTree as ET

                            gpx_dir = os.path.join(tempfile.gettempdir(), "rad-touren-gpx")
                            os.makedirs(gpx_dir, exist_ok=True)
                            gpx_path = os.path.join(gpx_dir, "latest-route.gpx")
                            with open(gpx_path, "w", encoding="utf-8") as f:
                                f.write(gpx_content)
                            logger.info("GPX saved to %s", gpx_path)
                            # Replace gpx content with file path for the LLM
                            result["gpx_path"] = gpx_path

                            # Extract elevation profile from GPX
                            try:
                                gpx_ns = "http://www.topografix.com/GPX/1/1"
                                root = ET.fromstring(gpx_content)
                                points: list[tuple[float, float, float]] = []
                                for trkpt in root.findall(f".//{{{gpx_ns}}}trkpt"):
                                    lat_e = float(trkpt.get("lat", "0"))
                                    lon_e = float(trkpt.get("lon", "0"))
                                    ele_elem = trkpt.find(f"{{{gpx_ns}}}ele")
                                    if ele_elem is not None and ele_elem.text:
                                        ele = float(ele_elem.text)
                                        points.append((lat_e, lon_e, ele))

                                if len(points) >= 2:
                                    # Calculate cumulative distance and sample ~200 points
                                    cum_dist = [0.0]
                                    for i in range(1, len(points)):
                                        dlat = (points[i][0] - points[i - 1][0]) * 111320
                                        dlon = (
                                            (points[i][1] - points[i - 1][1])
                                            * 111320
                                            * math.cos(math.radians(points[i][0]))
                                        )
                                        cum_dist.append(
                                            cum_dist[-1] + math.sqrt(dlat**2 + dlon**2)
                                        )

                                    total_m = cum_dist[-1]
                                    # Sample to ~200 points for the chart
                                    step = max(1, len(points) // 200)
                                    elevation_data: list[list[float]] = []
                                    for i in range(0, len(points), step):
                                        elevation_data.append(
                                            [round(cum_dist[i] / 1000, 2), round(points[i][2], 1)]
                                        )
                                    # Always include last point
                                    if elevation_data[-1][0] != round(total_m / 1000, 2):
                                        elevation_data.append(
                                            [round(total_m / 1000, 2), round(points[-1][2], 1)]
                                        )

                                    yield {
                                        "event": "elevation",
                                        "data": {"profile": elevation_data},
                                    }
                                    logger.info(
                                        "Elevation profile: %d points, %.1f km",
                                        len(elevation_data),
                                        total_m / 1000,
                                    )
                            except Exception as exc:
                                logger.debug("Failed to extract elevation: %s", exc)
                        # Strip large fields before sending to LLM (context savings)
                        result.pop("geometry", None)
                        result.pop("gpx", None)
                    elif _is_geocode_tool(tool_name):
                        results_list: list[dict[str, Any]] = result.get("results", [])
                        if results_list:
                            coords = results_list[0].get("coordinates", [])
                            if len(coords) == 2:
                                yield {
                                    "event": "map",
                                    "data": {"waypoints": [[coords[1], coords[0]]]},
                                }
                    elif _is_poi_tool(tool_name):
                        # Parse POI coordinates, names, and categories from text result
                        text = result.get("text", "")
                        logger.debug("POI tool result keys: %s", list(result.keys()))
                        if text:
                            poi_list_from_text: list[dict[str, Any]] = []
                            for m in re.finditer(
                                r"\*\*(.+?)\*\*\s*\(([^)]*)\)\s*\[(-?\d+\.\d+),\s*(-?\d+\.\d+)\]",
                                text,
                            ):
                                name_val = m.group(1)
                                category_val = m.group(2)
                                lat_val = float(m.group(3))
                                lon_val = float(m.group(4))
                                poi_list_from_text.append(
                                    {
                                        "lat": lat_val,
                                        "lon": lon_val,
                                        "name": name_val,
                                        "category": category_val,
                                    }
                                )
                            if poi_list_from_text:
                                logger.info(
                                    "Emitting %d POI markers from overpass text",
                                    len(poi_list_from_text),
                                )
                                yield {
                                    "event": "map",
                                    "data": {"pois": poi_list_from_text},
                                }
                            else:
                                logger.warning(
                                    "POI tool returned text but no POIs parsed: %s",
                                    text[:200],
                                )
                        else:
                            logger.warning(
                                "POI tool result has no 'text' key, keys: %s",
                                list(result.keys()),
                            )

                result_str = json.dumps(result, ensure_ascii=False, default=str)
                # Truncate very large results to prevent context bloat
                if len(result_str) > 8000:
                    logger.info(
                        "Truncating %s result from %d to 8000 chars", tool_name, len(result_str)
                    )
                    result_str = result_str[:8000] + '..."}'
                logger.debug("Tool %s result: %s", tool_name, result_str[:200])
            except Exception as e:
                logger.error("Tool %s failed: %s", tool_name, e)
                result_str = json.dumps({"error": str(e)})

            tool_results.append(
                types.Part.from_function_response(
                    name=tool_name,
                    response=json.loads(result_str),
                )
            )

        # Add tool results to conversation
        contents.append(types.Content(role="user", parts=tool_results))

    # Max iterations reached
    logger.warning("Max iterations (%d) reached", max_iterations)
    yield {"event": "error", "data": {"error": i18n_msg("max_iterations", lang)}}
