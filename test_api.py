from fastapi.testclient import TestClient

from api import app

client = TestClient(app)


def test_home_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "running"


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_player_search_finds_mbappe():
    response = client.get(
        "/players/search",
        params={"q": "mbappe", "limit": 10},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["count"] > 0
    assert any(
        player["player_id"] == 342229
        for player in data["results"]
    )


def test_similar_players_returns_results():
    response = client.get("/players/342229/similar")

    assert response.status_code == 200

    data = response.json()
    assert data["player_id"] == 342229
    assert data["count"] > 0
    assert len(data["results"]) > 0


def test_unknown_player_returns_404():
    response = client.get("/players/999999999/similar")

    assert response.status_code == 404
    assert response.json()["detail"] == "Player not found"