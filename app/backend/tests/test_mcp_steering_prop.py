"""Property test: Steering Passthrough.

**Validates: Requirements 6.1**

For any steering file content containing `mcp_` prefixed tool names, loading
the content through the simplified steering module SHALL preserve all `mcp_`
prefixed names unchanged in the output.
"""

from hypothesis import given, settings
from hypothesis import strategies as st

from steering import build_system_prompt


# --- Strategies ---

# Generate valid MCP server prefixes (lowercase, no hyphens in final form)
_server_prefixes = st.sampled_from(
    [
        "brouter",
        "open_meteo",
        "vbb",
        "overpass",
        "openrouteservice",
        "osrm",
        "wikivoyage",
        "waymarkedtrails",
    ]
)

# Generate valid tool name suffixes (lowercase + underscores)
_tool_suffixes = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz_",
    min_size=3,
    max_size=20,
).filter(lambda s: not s.startswith("_") and not s.endswith("_") and "__" not in s)


@st.composite
def mcp_tool_name(draw: st.DrawFn) -> str:
    """Generate a valid mcp_ prefixed tool name."""
    prefix = draw(_server_prefixes)
    suffix = draw(_tool_suffixes)
    return f"mcp_{prefix}_{suffix}"


@st.composite
def mcp_tool_names_list(draw: st.DrawFn) -> list[str]:
    """Generate a list of 1-10 unique mcp_ prefixed tool names."""
    names = draw(st.lists(mcp_tool_name(), min_size=1, max_size=10, unique=True))
    return names


@given(tool_names=mcp_tool_names_list())
@settings(max_examples=100, deadline=None)
def test_mcp_tool_names_preserved_in_system_prompt(
    tool_names: list[str],
) -> None:
    """Property 8: All mcp_ prefixed tool names appear unchanged in the output.

    **Validates: Requirements 6.1**
    """
    # Build the system prompt with the generated tool names
    prompt = build_system_prompt(
        tool_names=tool_names,
        language="de",
        user_message="",
    )

    # Every mcp_ prefixed tool name must appear verbatim in the output
    for name in tool_names:
        assert name in prompt, (
            f"Tool name '{name}' was not preserved in the system prompt output. "
            f"Expected it to appear unchanged but it was missing or rewritten."
        )


@given(tool_names=mcp_tool_names_list())
@settings(max_examples=50, deadline=None)
def test_mcp_tool_names_not_rewritten(
    tool_names: list[str],
) -> None:
    """Property 8 (supplementary): No mcp_ names are stripped or altered.

    **Validates: Requirements 6.1**

    Verifies that the count of mcp_ prefixed names in the output is at least
    as many as the input — none were removed or rewritten to non-mcp_ forms.
    """
    prompt = build_system_prompt(
        tool_names=tool_names,
        language="en",
        user_message="plan a bike tour",
    )

    # Each tool name must appear at least once in the prompt
    for name in tool_names:
        occurrences = prompt.count(name)
        assert occurrences >= 1, (
            f"Tool name '{name}' appears {occurrences} times in prompt, "
            f"expected at least 1. The name may have been rewritten or removed."
        )
