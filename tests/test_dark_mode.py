def test_dark_mode_css_present(client):
    rv = client.get("/login")
    assert b'data-theme' in rv.data
