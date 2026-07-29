def test_skip_link_present(client):
    rv = client.get("/login")
    assert b'skip-link' in rv.data
    assert b'aria-label' in rv.data
