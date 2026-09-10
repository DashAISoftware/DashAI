"""Tests for docs/scripts/generate_components.py."""

import sys
from pathlib import Path

# Add docs/scripts to path so we can import the generator
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "docs" / "scripts"))


# Helpers that don't require importing the full DashAI stack
class FakeMultilingualString:
    def __init__(self, en, es=None, pt=None):
        self.en = en
        self.es = es
        self.pt = pt

    def get(self, lang):
        if lang == "es" and self.es:
            return self.es
        if lang == "pt" and self.pt:
            return self.pt
        return self.en


# ------------------------------------------------------------------ #
# _extract_text                                                       #
# ------------------------------------------------------------------ #
def test_extract_text_from_multilingual_string():
    from generate_components import _extract_text

    ms = FakeMultilingualString(en="English text", es="Texto en español")
    assert _extract_text(ms) == "English text"


def test_extract_text_from_plain_string():
    from generate_components import _extract_text

    assert _extract_text("plain string") == "plain string"


def test_extract_text_from_none_returns_empty():
    from generate_components import _extract_text

    assert _extract_text(None) == ""


def test_extract_text_from_missing_attr_returns_fallback():
    from generate_components import _extract_text

    sentinel = object()  # has no .get, not a str
    assert _extract_text(sentinel, fallback="fallback") == "fallback"


# ------------------------------------------------------------------ #
# _get_display_name                                                   #
# ------------------------------------------------------------------ #
def test_get_display_name_from_attribute():
    from generate_components import _get_display_name

    class FakeCls:
        DISPLAY_NAME = FakeMultilingualString(en="My Model")

    assert _get_display_name(FakeCls) == "My Model"


def test_get_display_name_falls_back_to_class_name():
    from generate_components import _get_display_name

    class FakeCls:
        pass

    assert _get_display_name(FakeCls) == "FakeCls"


# ------------------------------------------------------------------ #
# _get_description                                                    #
# ------------------------------------------------------------------ #
def test_get_description_from_docstring():
    from generate_components import _get_description

    class FakeCls:
        """Docstring description."""

    assert _get_description(FakeCls) == "Docstring description."


def test_get_description_returns_empty_when_nothing():
    from generate_components import _get_description

    class FakeCls:
        pass

    assert _get_description(FakeCls) == ""


def test_get_description_strips_multiline_docstring():
    from generate_components import _get_description

    class FakeCls:
        """
        First line of description.

        Second paragraph.
        """

    result = _get_description(FakeCls)
    assert result.startswith("First line")
    assert "\n    " not in result  # no raw indentation preserved


# ------------------------------------------------------------------ #
# _get_module_path                                                    #
# ------------------------------------------------------------------ #
def test_get_module_path_strips_file_stem():
    from generate_components import _get_module_path

    class FakeCls:
        pass

    FakeCls.__module__ = "DashAI.back.models.hugging_face.distilbert_transformer"
    assert _get_module_path(FakeCls) == "DashAI.back.models.hugging_face"


def test_get_module_path_handles_top_level_module():
    from generate_components import _get_module_path

    class FakeCls:
        pass

    FakeCls.__module__ = "mymodule"
    assert _get_module_path(FakeCls) == "mymodule"


# ------------------------------------------------------------------ #
# _get_compatible_components                                          #
# ------------------------------------------------------------------ #
def test_get_compatible_components_returns_list():
    from generate_components import _get_compatible_components

    class FakeCls:
        COMPATIBLE_COMPONENTS = ["TaskA", "TaskB"]

    assert _get_compatible_components(FakeCls) == ["TaskA", "TaskB"]


def test_get_compatible_components_returns_empty_list_when_missing():
    from generate_components import _get_compatible_components

    class FakeCls:
        pass

    assert _get_compatible_components(FakeCls) == []


# ------------------------------------------------------------------ #
# _get_schema_params: JSON Schema -> list of param dicts             #
# ------------------------------------------------------------------ #
def test_get_schema_params_parses_properties():
    from generate_components import _get_schema_params

    class FakeCls:
        @classmethod
        def get_schema(cls):
            return {
                "properties": {
                    "C": {
                        "type": "number",
                        "default": 1.0,
                        "description": "Regularization",
                    },
                    "kernel": {
                        "type": "string",
                        "default": "rbf",
                        "description": "Kernel type",
                    },
                }
            }

    params = _get_schema_params(FakeCls)
    assert len(params) == 2
    assert params[0]["name"] == "C"
    assert params[0]["type"] == "number"
    assert params[0]["default"] == "1.0"
    assert params[0]["description"] == "Regularization"


def test_get_schema_params_returns_empty_when_no_schema():
    from generate_components import _get_schema_params

    class FakeCls:
        @classmethod
        def get_schema(cls):
            return None

    assert _get_schema_params(FakeCls) == []


def test_get_schema_params_returns_empty_when_get_schema_raises():
    from generate_components import _get_schema_params

    class FakeCls:
        @classmethod
        def get_schema(cls):
            raise AttributeError("No schema")

    assert _get_schema_params(FakeCls) == []


def test_get_schema_params_returns_empty_when_method_missing():
    from generate_components import _get_schema_params

    class FakeCls:
        pass  # no get_schema method at all

    assert _get_schema_params(FakeCls) == []


# ------------------------------------------------------------------ #
# _get_methods                                                        #
# ------------------------------------------------------------------ #
def test_get_methods_includes_own_methods():
    from generate_components import _get_methods

    class MyClass:
        def my_method(self, x: int) -> str:
            """Do something.

            Parameters
            ----------
            x : int
                The input.

            Returns
            -------
            str
                The output.
            """
            return str(x)

    methods = _get_methods(MyClass)
    names = [m["name"] for m in methods]
    assert "my_method" in names


def test_get_methods_excludes_dunder_methods():
    from generate_components import _get_methods

    class MyClass:
        def __init__(self):
            pass

        def public_method(self):
            pass

    methods = _get_methods(MyClass)
    names = [m["name"] for m in methods]
    assert "__init__" not in names
    assert "public_method" in names


def test_get_methods_excludes_private_methods():
    from generate_components import _get_methods

    class MyClass:
        def _private(self):
            pass

        def public(self):
            pass

    methods = _get_methods(MyClass)
    names = [m["name"] for m in methods]
    assert "_private" not in names
    assert "public" in names


def test_get_methods_annotates_inherited_source_class():
    from generate_components import _get_methods

    class Base:
        def base_method(self):
            """Base method."""

    class Child(Base):
        def child_method(self):
            """Child method."""

    methods = _get_methods(Child)
    by_name = {m["name"]: m for m in methods}
    assert by_name["base_method"]["defined_on"] == "Base"
    assert by_name["child_method"]["defined_on"] == "Child"


def test_get_methods_excludes_object_methods():
    from generate_components import _get_methods

    class MyClass:
        def my_method(self):
            pass

    methods = _get_methods(MyClass)
    names = [m["name"] for m in methods]
    assert "__class__" not in names


# ------------------------------------------------------------------ #
# _render_component_mdx                                              #
# ------------------------------------------------------------------ #
def _make_info(**overrides):
    """Return a minimal valid info dict for _render_component_mdx."""
    base = {
        "class_name": "StandardScaler",
        "type": "Converter",
        "display_name": "Standard Scaler",
        "description": "Standardize features.",
        "module_path": "DashAI.back.converters",
        "params": [],
        "methods": [],
        "compatible": [],
        "class_lookup": {},
    }
    base.update(overrides)
    return base


def test_render_component_mdx_contains_title():
    from generate_components import _render_component_mdx

    mdx = _render_component_mdx(_make_info())
    assert 'title: "StandardScaler"' in mdx
    assert "# StandardScaler" in mdx


def test_render_component_mdx_contains_type_badge():
    from generate_components import _render_component_mdx

    mdx = _render_component_mdx(_make_info())
    assert "sk-badge" in mdx
    assert "Converter" in mdx


def test_render_component_mdx_contains_module_path():
    from generate_components import _render_component_mdx

    mdx = _render_component_mdx(_make_info())
    assert "DashAI.back.converters" in mdx
    assert "sk-sig" in mdx


def test_render_component_mdx_contains_params_section():
    from generate_components import _render_component_mdx

    info = _make_info(
        class_name="SVC",
        type="Model",
        params=[
            {
                "name": "C",
                "type": "number",
                "default": "1.0",
                "description": "Regularization",
            }
        ],
    )
    mdx = _render_component_mdx(info)
    assert "## Parameters" in mdx
    assert "C" in mdx
    assert "Regularization" in mdx


def test_render_component_mdx_skips_params_when_empty():
    from generate_components import _render_component_mdx

    mdx = _render_component_mdx(_make_info())
    assert "## Parameters" not in mdx


def test_render_component_mdx_contains_compatible_section():
    from generate_components import _render_component_mdx

    info = _make_info(
        class_name="F1",
        type="Metric",
        compatible=["TextClassificationTask", "TabularClassificationTask"],
    )
    mdx = _render_component_mdx(info)
    assert "## Compatible with" in mdx
    assert "TextClassificationTask" in mdx


def test_render_component_mdx_skips_sig_when_no_module_path():
    from generate_components import _render_component_mdx

    mdx = _render_component_mdx(_make_info(module_path=""))
    assert "sk-sig" not in mdx


# ------------------------------------------------------------------ #
# _render_index_mdx                                                   #
# ------------------------------------------------------------------ #
def test_render_index_mdx_lists_all_components():
    from generate_components import _render_index_mdx

    components = [
        {
            "class_name": "SVC",
            "display_name": "SVC",
            "description": "Support vector classifier.",
        },
        {
            "class_name": "DecisionTree",
            "display_name": "Decision Tree",
            "description": "Tree-based classifier.",
        },
    ]
    mdx = _render_index_mdx("Model", components)
    assert "SVC" in mdx
    assert "DecisionTree" in mdx
    assert "Support vector classifier" in mdx


# ------------------------------------------------------------------ #
# _is_pipeline_node                                                   #
# ------------------------------------------------------------------ #
def test_is_pipeline_node_returns_true_for_pipeline_module():
    from generate_components import _is_pipeline_node

    class FakeCls:
        pass

    FakeCls.__module__ = "DashAI.back.pipeline.something"

    assert _is_pipeline_node(FakeCls) is True


def test_is_pipeline_node_returns_false_for_other_module():
    from generate_components import _is_pipeline_node

    class FakeCls:
        pass

    FakeCls.__module__ = "DashAI.back.models.svc"

    assert _is_pipeline_node(FakeCls) is False


# ------------------------------------------------------------------ #
# _format_default                                                     #
# ------------------------------------------------------------------ #
def test_format_default_reads_placeholder_key():
    from generate_components import _format_default

    prop = {"placeholder": "rbf", "description": "Kernel type"}
    assert _format_default(prop) == "rbf"


def test_format_default_falls_back_to_default_key():
    from generate_components import _format_default

    prop = {"default": "linear", "description": "Kernel type"}
    assert _format_default(prop) == "linear"


def test_format_default_returns_dash_when_neither():
    from generate_components import _format_default

    prop = {"description": "No default"}
    assert _format_default(prop) == "-"


# ------------------------------------------------------------------ #
# _escape_table_cell                                                  #
# ------------------------------------------------------------------ #
def test_escape_table_cell_escapes_pipe():
    from generate_components import _escape_table_cell

    assert _escape_table_cell("a|b") == "a\\|b"


def test_escape_table_cell_escapes_curly_braces():
    from generate_components import _escape_table_cell

    assert _escape_table_cell("{array}") == "&#123;array&#125;"


def test_escape_table_cell_escapes_angle_brackets():
    from generate_components import _escape_table_cell

    assert _escape_table_cell("a < b > c") == "a &lt; b &gt; c"
