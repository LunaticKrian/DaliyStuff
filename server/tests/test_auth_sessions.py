"""鉴权会话化端到端测试：轮换、复用检测、登出、设备列表/踢出、改密码级联。"""
import pytest

CREDS = {"username": "tester", "password": "secret123", "email": "t@example.com"}


async def _register(client, device="A", platform="desktop"):
    r = await client.post(
        "/api/auth/register",
        json=CREDS,
        headers={"X-Device-Name": f"Device-{device}", "X-Device-Platform": platform},
    )
    assert r.status_code == 201, r.text
    return r.json()


async def _login(client, device="A", platform="desktop"):
    r = await client.post(
        "/api/auth/login",
        json={"username": CREDS["username"], "password": CREDS["password"]},
        headers={"X-Device-Name": f"Device-{device}", "X-Device-Platform": platform},
    )
    assert r.status_code == 200, r.text
    return r.json()


def _auth(tokens):
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def test_register_me_and_sessions_requires_auth(client):
    tokens = await _register(client)
    me = await client.get("/api/auth/me", headers=_auth(tokens))
    assert me.status_code == 200
    assert me.json()["username"] == CREDS["username"]

    # 无 token 访问受保护端点 → 401
    no_auth = await client.get("/api/auth/sessions")
    assert no_auth.status_code == 401


async def test_refresh_rotates_and_detects_reuse(client):
    tokens = await _register(client)
    r1 = tokens["refresh_token"]

    refreshed = await client.post("/api/auth/refresh", json={"refresh_token": r1})
    assert refreshed.status_code == 200, refreshed.text
    r2 = refreshed.json()["refresh_token"]
    assert r2 != r1  # 已轮换

    # 旧 refresh 复用 → 401，且会话被吊销
    reused = await client.post("/api/auth/refresh", json={"refresh_token": r1})
    assert reused.status_code == 401

    # 会话已吊销：新 refresh 与原 access 均失效
    assert (await client.post("/api/auth/refresh", json={"refresh_token": r2})).status_code == 401
    assert (await client.get("/api/auth/me", headers=_auth(tokens))).status_code == 401


async def test_logout_revokes_session(client):
    tokens = await _register(client)
    out = await client.post("/api/auth/logout", headers=_auth(tokens))
    assert out.status_code == 200
    assert (await client.get("/api/auth/me", headers=_auth(tokens))).status_code == 401


async def test_sessions_list_and_revoke_other_device(client):
    await _register(client, device="A")
    a = await _login(client, device="A")
    b = await _login(client, device="B")

    listed = await client.get("/api/auth/sessions", headers=_auth(a))
    assert listed.status_code == 200
    items = listed.json()
    assert len(items) >= 2
    assert any(i["is_current"] for i in items)

    b_item = next(i for i in items if i["device_name"] == "Device-B")
    rev = await client.delete(f"/api/auth/sessions/{b_item['id']}", headers=_auth(a))
    assert rev.status_code == 200

    # B 被踢；A 仍有效
    assert (await client.get("/api/auth/me", headers=_auth(b))).status_code == 401
    assert (await client.get("/api/auth/me", headers=_auth(a))).status_code == 200


async def test_password_change_revokes_other_devices(client):
    await _register(client, device="A")
    a = await _login(client, device="A")
    b = await _login(client, device="B")

    pw = await client.put(
        "/api/auth/password",
        json={"old_password": CREDS["password"], "new_password": "newpass456"},
        headers=_auth(a),
    )
    assert pw.status_code == 200

    # B 被踢；A 保留
    assert (await client.get("/api/auth/me", headers=_auth(b))).status_code == 401
    assert (await client.get("/api/auth/me", headers=_auth(a))).status_code == 200
