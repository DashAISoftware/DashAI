from DashAI.back.dependencies.registry.relationship_manager import RelationshipManager


def test_add_default_relation_type_is_bidirectional():
    rm = RelationshipManager()
    rm.add_relationship("A", "B")
    assert rm.get("A", "compatible_components") == ["B"]
    assert rm.get("B", "compatible_components") == ["A"]


def test_relation_types_are_isolated():
    rm = RelationshipManager()
    rm.add_relationship("Model", "Task", "compatible_components")
    rm.add_relationship("Model", "HFCred", "required_credentials")
    assert rm.get("Model", "compatible_components") == ["Task"]
    assert rm.get("Model", "required_credentials") == ["HFCred"]
    # reverse lookup of who requires the credential
    assert rm.get("HFCred", "required_credentials") == ["Model"]


def test_get_missing_returns_empty_list():
    rm = RelationshipManager()
    assert rm.get("X", "compatible_components") == []


def test_relations_property_is_nested():
    rm = RelationshipManager()
    rm.add_relationship("A", "B")
    assert rm.relations == {
        "A": {"compatible_components": ["B"]},
        "B": {"compatible_components": ["A"]},
    }


def test_remove_relationship_with_type():
    rm = RelationshipManager()
    rm.add_relationship("A", "B", "required_credentials")
    rm.remove_relationship("A", "B", "required_credentials")
    assert rm.get("A", "required_credentials") == []
    assert rm.get("B", "required_credentials") == []
