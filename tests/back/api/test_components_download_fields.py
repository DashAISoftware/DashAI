"""Test that components API exposes download-related fields."""


def test_components_list_includes_download_fields(client):
    """Verify that the components list endpoint includes download fields.

    Parameters
    ----------
    client : TestClient
        The FastAPI test client fixture.
    """
    response = client.get("/api/v1/component/", params={"select_types": ["Model"]})
    assert response.status_code == 200
    components = response.json()
    assert components, "expected at least one Model component"
    for component in components:
        assert "downloaded" in component
        assert "requires_download" in component["metadata"]
        assert "download_size_bytes" in component["metadata"]


def test_component_by_id_includes_download_fields(client):
    """Verify that the single component endpoint includes download fields.

    Parameters
    ----------
    client : TestClient
        The FastAPI test client fixture.
    """
    # Get a Model component to test
    response = client.get("/api/v1/component/", params={"select_types": ["Model"]})
    assert response.status_code == 200
    components = response.json()
    assert components, "expected at least one Model component"

    # Test the first component via direct ID endpoint
    component_id = components[0]["name"]
    response = client.get(f"/api/v1/component/{component_id}/")
    assert response.status_code == 200
    component = response.json()
    assert "downloaded" in component
    assert "requires_download" in component["metadata"]
    assert "download_size_bytes" in component["metadata"]
