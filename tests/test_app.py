from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_full_awdp_flow():
    reg = client.post("/auth/register", json={"username": "alice", "password": "strongpass"})
    assert reg.status_code == 200
    token = reg.json()["access_token"]

    team = client.post("/teams", headers=auth_header(token), json={"name": "RedTeam"})
    assert team.status_code == 200
    invite_code = team.json()["invite_code"]

    reg2 = client.post("/auth/register", json={"username": "bob", "password": "strongpass"})
    bob_token = reg2.json()["access_token"]

    join = client.post(f"/teams/{invite_code}/join", headers=auth_header(bob_token))
    assert join.status_code == 200

    challenges = client.get("/challenges")
    assert challenges.status_code == 200
    challenge_id = challenges.json()[0]["id"]

    alloc = client.post(
        "/containers/allocate",
        headers=auth_header(token),
        json={"challenge_id": challenge_id},
    )
    assert alloc.status_code == 200
    assert alloc.json()["status"] == "running"

    wrong_flag = client.post(
        "/flags/submit",
        headers=auth_header(token),
        json={"challenge_id": challenge_id, "flag": "DINO{wrong}"},
    )
    assert wrong_flag.status_code == 200
    assert wrong_flag.json()["success"] is False

    correct_flag = client.post(
        "/flags/submit",
        headers=auth_header(token),
        json={"challenge_id": challenge_id, "flag": "DINO{demo_flag_1}"},
    )
    assert correct_flag.status_code == 200
    assert correct_flag.json()["success"] is True
    assert correct_flag.json()["awarded_points"] > 0

    patch = client.post(
        "/patches/submit",
        headers=auth_header(token),
        json={"challenge_id": challenge_id, "patch_content": "# FIXED: sanitize input"},
    )
    assert patch.status_code == 200
    assert patch.json()["success"] is True

    board = client.get("/leaderboard")
    assert board.status_code == 200
    top = board.json()[0]
    assert top["team_name"] == "RedTeam"
    assert top["score"] >= 250


def test_frontend_index_page():
    res = client.get("/")
    assert res.status_code == 200
    assert "Dino AWDP Platform" in res.text
