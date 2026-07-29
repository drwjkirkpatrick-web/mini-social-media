def test_help_page(client):
    rv = client.get("/help")
    assert rv.status_code == 200
    assert b"Getting Started" in rv.data
