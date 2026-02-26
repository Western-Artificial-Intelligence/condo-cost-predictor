from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_get_map_data_shape_and_fields():
    response = client.get("/api/map-data")
    assert response.status_code == 200
    payload = response.json()

    assert len(payload) == 158
    agincourt = next(item for item in payload if item["neighbourhood"] == "Agincourt North")

    assert agincourt["predicted_tier"] == 1
    assert agincourt["cluster_id"] == 1
    assert agincourt["cluster_label"] == "Connected Family Neighborhood"
    assert agincourt["geometry"]["type"] in {"Polygon", "MultiPolygon"}


def test_get_history_returns_15_year_points_for_known_neighbourhood():
    response = client.get("/api/neighbourhood/Agincourt%20North/history")
    assert response.status_code == 200
    payload = response.json()

    assert payload["neighbourhood"] == "Agincourt North"
    assert len(payload["history"]) == 15
    assert payload["history"][0]["year"] == 2010
    assert payload["history"][-1]["year"] == 2024
    assert len({point["year"] for point in payload["history"]}) == 15


def test_get_history_unknown_neighbourhood_returns_404():
    response = client.get("/api/neighbourhood/Not%20A%20Real%20Place/history")
    assert response.status_code == 404
    assert "Unknown neighbourhood" in response.json()["detail"]
