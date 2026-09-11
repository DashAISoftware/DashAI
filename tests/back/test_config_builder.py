from DashAI.back.dependencies.config_builder import build_config_dict


def test_preprocessing_path_is_under_local_path(tmp_path):
    config = build_config_dict(local_path=tmp_path, logging_level="ERROR")
    assert config["PREPROCESSING_PATH"] == tmp_path / "preprocessing"
