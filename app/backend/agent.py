"""Gemini agent loop with tool calling and streaming."""

import json
from collections.abc import AsyncGenerator

from google import genai
from google.genai import types
from google.genai.errors import ClientError, ServerError

from steering import build_system_prompt
from tools import TOOL_DECLARATIONS, TOOL_REGISTRY


def create_client(api_key: str) -> genai.Client:
    """Create a Gemini client."""
    return genai.Client(api_key=api_key)


async def run_agent(
    client: genai.Client,
    user_message: str,
    chat_history: list[dict],
    tour_type: str = "road",
) -> AsyncGenerator[dict, None]:
    """Run the agent loop, yielding SSE events.

    Yields dicts with keys: {"event": str, "data": dict}
    """
    system_prompt = build_system_prompt(tour_type)

    # Build conversation contents
    contents = []
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
    max_iterations = 15
    for iteration in range(max_iterations):
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=contents,
                config=config,
            )
        except ClientError as e:
            if e.code == 429:
                yield {
                    "event": "error",
                    "data": {"error": "API-Quota erschöpft. Bitte warte einige Minuten oder prüfe dein Gemini-Kontingent."},
                }
            else:
                yield {
                    "event": "error",
                    "data": {"error": f"Gemini API-Fehler ({e.code}): {e.message or e!s}"},
                }
            return
        except ServerError as e:
            yield {
                "event": "error",
                "data": {"error": f"Gemini-Server nicht erreichbar ({e.code}). Bitte später erneut versuchen."},
            }
            return
        except Exception as e:
            yield {
                "event": "error",
                "data": {"error": f"Unerwarteter Fehler: {e!s}"},
            }
            return

        # Check if response has function calls
        candidate = response.candidates[0]
        parts = candidate.content.parts

        function_calls = [p for p in parts if p.function_call]

        if not function_calls:
            # No more tool calls — this is the final response
            text_parts = [p.text for p in parts if p.text]
            final_text = "\n".join(text_parts)
            yield {"event": "tour", "data": {"markdown": final_text}}
            yield {"event": "done", "data": {"iterations": iteration + 1}}
            return

        # Execute tool calls
        contents.append(candidate.content)
        tool_results = []

        for part in function_calls:
            fc = part.function_call
            tool_name = fc.name
            tool_args = dict(fc.args) if fc.args else {}

            yield {
                "event": "status",
                "data": {"message": f"🔧 {tool_name}({json.dumps(tool_args, ensure_ascii=False)[:100]})..."},
            }

            # Execute the tool
            tool_fn = TOOL_REGISTRY.get(tool_name)
            if tool_fn:
                try:
                    result = await tool_fn(**tool_args)
                    result_str = json.dumps(result, ensure_ascii=False, default=str)
                except Exception as e:
                    result_str = json.dumps({"error": str(e)})
            else:
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
    yield {"event": "error", "data": {"error": "Maximale Iterationen erreicht. Bitte versuche eine kürzere Anfrage."}}
