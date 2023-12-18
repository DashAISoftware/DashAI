from collections import defaultdict

from DashAI.back.services.registry.relationship_manager import RelationshipManager


def test_relationship_manager_add_relations():
    test_relationship_manager = RelationshipManager()

    assert isinstance(test_relationship_manager.relations, dict)
    assert isinstance(test_relationship_manager._relations, defaultdict)
    assert test_relationship_manager.relations == {}
    assert test_relationship_manager._relations == defaultdict(list)

    test_relationship_manager.add_relationship("Component1", "Task1")
    test_relationship_manager.add_relationship("Component2", "Task1")
    test_relationship_manager.add_relationship("Component3", "Task2")

    assert test_relationship_manager.relations == {
        "Component1": ["Task1"],
        "Task1": ["Component1", "Component2"],
        "Component2": ["Task1"],
        "Component3": ["Task2"],
        "Task2": ["Component3"],
    }


def test_relationship_manager__getitem__():
    test_relationship_manager = RelationshipManager()

    test_relationship_manager.add_relationship("Component1", "Task1")
    test_relationship_manager.add_relationship("Component2", "Task1")
    test_relationship_manager.add_relationship("Component3", "Task2")

    assert test_relationship_manager["Component1"] == ["Task1"]
    assert test_relationship_manager["Component2"] == ["Task1"]
    assert test_relationship_manager["Component3"] == ["Task2"]
    assert test_relationship_manager["Task1"] == ["Component1", "Component2"]
    assert test_relationship_manager["Task2"] == ["Component3"]


def test_relationship_manager__getitem__unexistant_component():
    test_relationship_manager = RelationshipManager()
    assert test_relationship_manager["UnexistantComponent"] == []
