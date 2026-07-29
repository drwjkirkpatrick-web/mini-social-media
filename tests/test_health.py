def test_health_endpoint(client):
    rv = client.get("/health")
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["status"] == "ok"
    assert data["version"] == "0.3.0"
    assert data["db"] == "connected"


def test_manifest_endpoint(client):
    rv = client.get("/manifest.json")
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["name"] == "mini-social-media"
    assert data["display"] == "standalone"


def test_sw_js_endpoint(client):
    rv = client.get("/sw.js")
    assert rv.status_code == 200
    assert b"mini-social-v0.3.0" in rv.data


def test_offline_page(client):
    rv = client.get("/offline")
    assert rv.status_code == 200
    assert b"Offline" in rv.data
