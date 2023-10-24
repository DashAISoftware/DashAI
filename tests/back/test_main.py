def test_app_docs(client):
    response = client.get("/app/")
    assert response.status_code == 200
