def test_mobile_client_page_loads(client):
    resp = client.get("/client")
    assert resp.status_code == 200
    assert "颐和园导览" in resp.text
    assert "data-switch=\"guide\"" in resp.text
    assert "data-switch=\"ask\"" in resp.text
    assert "data-switch=\"vision\"" in resp.text
    assert "/static/client/app.js" in resp.text


def test_mobile_client_assets_load(client):
    css = client.get("/static/client/styles.css")
    js = client.get("/static/client/app.js")
    assert css.status_code == 200
    assert js.status_code == 200
    assert "WebSocket" in js.text
    assert "BMapGL" in js.text
    assert "switchView" in js.text
    assert "/api/v1/config/map" in js.text


def test_map_config_endpoint(client):
    resp = client.get("/api/v1/config/map")
    assert resp.status_code == 200
    data = resp.json()
    assert "provider" in data
    assert "baidu_browser_ak" in data
