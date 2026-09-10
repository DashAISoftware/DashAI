from DashAI.back.config import DefaultSettings
from DashAI.back.dependencies.config_builder import build_config_dict


def test_default_settings_has_component_path():
    assert DefaultSettings().COMPONENT_PATH == "components"


def test_component_path_resolved_under_local_path(tmp_path):
    config = build_config_dict(local_path=tmp_path, logging_level="INFO")
    assert config["COMPONENT_PATH"] == tmp_path / "components"
