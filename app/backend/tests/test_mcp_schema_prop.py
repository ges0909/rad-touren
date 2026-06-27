"""Property test: Schema Conversion Correctness.

**Validates: Requirements 2.2, 4.1, 4.3**

For any valid MCP tool schema with a name, description, and inputSchema,
converting it to a Gemini FunctionDeclaration SHALL produce a dict with:
(a) name matching `mcp_<prefix>_<original_name>` with all hyphens replaced
by underscores, (b) the original description preserved, and (c) parameters
matching the inputSchema structure (type, properties, required).
"""

from hypothesis import given, settings
from hypothesis import strategies as st
from mcp_manager import MCPManager

# --- Strategies ---

# Tool names: alphabet + underscores + hyphens, min 1 char
tool_names = st.text(
    alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyz_-"),
    min_size=1,
    max_size=30,
)

# Prefixes: alphabet + underscores, min 1 char
prefixes = st.text(
    alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyz_"),
    min_size=1,
    max_size=20,
)

# Descriptions: arbitrary text
descriptions = st.text(min_size=0, max_size=100)

# Property type values that Gemini/JSON Schema supports
property_types = st.sampled_from(["string", "number", "integer", "boolean"])

# Generate a dict of property names → {"type": <type>}
schema_properties = st.dictionaries(
    keys=st.text(
        alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyz_"),
        min_size=1,
        max_size=15,
    ),
    values=property_types.map(lambda t: {"type": t}),
    min_size=0,
    max_size=5,
)


@st.composite
def input_schemas(draw: st.DrawFn) -> dict:
    """Generate a valid inputSchema with properties and a subset as required."""
    props = draw(schema_properties)
    if not props:
        return {"type": "object", "properties": props}

    # Required is a subset of property keys
    keys = list(props.keys())
    required = draw(st.lists(st.sampled_from(keys), unique=True, max_size=len(keys)))

    schema: dict = {"type": "object", "properties": props}
    if required:
        schema["required"] = required
    return schema


@given(
    name=tool_names,
    prefix=prefixes,
    description=descriptions,
    input_schema=input_schemas(),
)
@settings(max_examples=200, deadline=None)
def test_schema_conversion_correctness(
    name: str, prefix: str, description: str, input_schema: dict
) -> None:
    """Property 3: Schema conversion produces correct name, description, and parameters.

    **Validates: Requirements 2.2, 4.1, 4.3**
    """
    manager = MCPManager(configs=[])

    tool = {
        "name": name,
        "description": description,
        "inputSchema": input_schema,
    }

    result = manager._mcp_schema_to_gemini(tool, prefix)

    # (a) Name matches mcp_<prefix>_<name> with all hyphens → underscores
    expected_name = f"mcp_{prefix}_{name}".replace("-", "_")
    assert result["name"] == expected_name, (
        f"Expected name '{expected_name}', got '{result['name']}'"
    )

    # (b) Description is preserved exactly
    assert result["description"] == description, (
        f"Expected description '{description}', got '{result['description']}'"
    )

    # (c) Parameters match inputSchema structure
    props = input_schema.get("properties", {})
    if props:
        assert "parameters" in result, "Expected 'parameters' key when inputSchema has properties"
        params = result["parameters"]

        # Type matches
        assert params["type"] == input_schema.get("type", "object")

        # Properties match
        assert params["properties"] == props, (
            f"Expected properties {props}, got {params['properties']}"
        )

        # Required matches if present in inputSchema
        required = input_schema.get("required")
        if required:
            assert params["required"] == required, (
                f"Expected required {required}, got {params.get('required')}"
            )
        else:
            assert "required" not in params, (
                f"Expected no 'required' key, but got {params.get('required')}"
            )

    # (5) No hyphens in the result name
    assert "-" not in result["name"], f"Result name '{result['name']}' contains hyphens"
