"""Gemini agent loop with tool calling and streaming."""

import asyncio
import json
import logging
from collections.abc import AsyncGenerator
from typing import Any

from google import genai
from google.genai import types
from google.genai.errors import ClientError, ServerError

from steering import build_system_prompt
from tools import TOOL_DECLARATIONS, TOOL_REGISTRY
from i18n import Lang, msg as i18n_msg

logger = logging.getLogger(__name__)

type SSEEvent = dict[str, Any]


def create_client(api_key: str) -> genai.Client:
    """Create a Gemini client."""
    return genai.Client(api_key=api_key)


async def _call_gemini_with_retry(
    client: genai.Client,
    contents: list[types.Content],
    config: types.GenerateContentConfig,
    max_retries: int = 3,
) -> Any:
    """Call Gemini with exponential backoff on 503/429 errors."""
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
                config=config,
            )
        except ServerError as e:
            if attempt < max_retries - 1 and e.code in (503, 500):
                wait = 2 ** (attempt + 1)  # 2s, 4s, 8s
                logger.warning("Gemini %d, retrying in %ds (attempt %d/%d)", e.code, wait, attempt + 1, max_retries)
                await asyncio.sleep(wait)
            else:
                raise
        except ClientError as e:
            if attempt < max_retries - 1 and e.code == 429:
                wait = min(2 ** (attempt + 2), 30)  # 4s, 8s, 16s
                logger.warning("Gemini 429, retrying in %ds (attempt %d/%d)", wait, attempt + 1, max_retries)
                await asyncio.sleep(wait)
            else:
                raise


async def run_agent(
    client: genai.Client,
    user_message: str,
    chat_history: list[dict[str, str]],
    tour_type: str = "road",
    language: str = "de",
) -> AsyncGenerator[SSEEvent, None]:
    """Run the agent loop, yielding SSE events.

    Yields dicts with keys: {"event": str, "data": dict}
    """
    system_prompt: str = build_system_prompt(tour_type, language=language, user_message=user_message)

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

    # Configure tools
    tools = types.Tool(function_declarations=[
        types.FunctionDeclaration(**decl) for decl in TOOL_DECLARATIONS
    ])

    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        tools=[tools],
        temperature=0.7,
    )

    # Agent loop: call LLM, execute tools, feed results back
    max_iterations: int = 15
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
                    "data": {"error": i18n_msg("api_error", lang, code=str(e.code), detail=e.message or str(e))},
                }
            return
        except ServerError as e:
            logger.error("Gemini ServerError %d: %s", e.code, e.message)
            yield {
                "event": "error",
                "data": {"error": i18n_msg("server_unavailable", lang, code=str(e.code))},
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
            # If blocked by safety, inform user
            if finish_reason and "SAFETY" in str(finish_reason):
                yield {"event": "error", "data": {"error": i18n_msg("unexpected_error", lang, detail="Response blocked by safety filter")}}
            else:
                yield {"event": "tour", "data": {"markdown": ""}}
            yield {"event": "done", "data": {"iterations": iteration + 1}}
            return

        parts = candidate.content.parts

        function_calls = [p for p in parts if p.function_call]

        if not function_calls:
            # No more tool calls — this is the final response
            text_parts: list[str] = [p.text for p in parts if p.text]
            final_text: str = "\n".join(text_parts)
            logger.info("Agent done: %d iterations, response %d chars", iteration + 1, len(final_text))
            yield {"event": "tour", "data": {"markdown": final_text}}
            yield {"event": "done", "data": {"iterations": iteration + 1}}
            return

        # Execute tool calls
        logger.info("Iteration %d: %d tool call(s)", iteration + 1, len(function_calls))
        contents.append(candidate.content)
        tool_results: list[types.Part] = []

        for part in function_calls:
            fc = part.function_call
            tool_name: str = fc.name
            tool_args: dict[str, Any] = dict(fc.args) if fc.args else {}

            logger.info("Tool call: %s(%s)", tool_name, json.dumps(tool_args, ensure_ascii=False)[:150])

            yield {
                "event": "status",
                "data": {"message": f"🔧 {tool_name}({json.dumps(tool_args, ensure_ascii=False)[:100]})..."},
            }

            # Execute the tool
            result_str: str
            tool_fn = TOOL_REGISTRY.get(tool_name)
            if tool_fn:
                try:
                    result: Any = await tool_fn(**tool_args)
                    result_str = json.dumps(result, ensure_ascii=False, default=str)
                    logger.debug("Tool %s result: %s", tool_name, result_str[:200])

                    # Emit map data events for geo tools
                    if tool_name == "geocode" and isinstance(result, dict):
                        results: list[dict[str, Any]] = result.get("results", [])
                        if results:
                            coords: list[float] = results[0].get("coordinates", [])
                            if len(coords) == 2:
                                yield {
                                    "event": "map",
                                    "data": {"waypoints": [[coords[1], coords[0]]]},
                                }
                    elif tool_name == "calculate_car_route" and isinstance(result, dict):
                        geometry: list[tuple[float, float]] | None = result.get("geometry")
                        if geometry:
                            yield {
                                "event": "map",
                                "data": {"route": [[lat, lon] for lat, lon in geometry]},
                            }
                        wps: list[list[float]] | None = result.get("waypoints")
                        if wps:
                            yield {
                                "event": "map",
                                "data": {"waypoints": wps},
                            }

                except Exception as e:
                    logger.error("Tool %s failed: %s", tool_name, e)
                    result_str = json.dumps({"error": str(e)})
            else:
                logger.warning("Unknown tool requested: %s", tool_name)
                result_str = json.dumps({"error": f"Unknown tool: {tool_name}"})

            tool_results.append(
                types.Part.from_function_response(
                    name=tool_name,
                    response=json.loads(result_str),
                )
            )

        # Add tool results to conversation
        contents.append(
            types.Content(role="user", parts=tool_results)
        )

    # Max iterations reached
    logger.warning("Max iterations (%d) reached", max_iterations)
    yield {"event": "error", "data": {"error": i18n_msg("max_iterations", lang)}}
