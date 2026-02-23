from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_list_neighbourhoods_has_full_snapshot():
    response = client.get("/api/neighbourhoods")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 158
    assert payload[0]["id"] == 1
    assert "name" in payload[0]


def test_predict_known_neighbourhood():
    response = client.post("/api/predict", json={"neighbourhood": "Agincourt North"})
    assert response.status_code == 200
    payload = response.json()

    assert payload["neighbourhood"] == "Agincourt North"
    assert payload["predicted_tier"] == 1
    assert payload["tier_label"] == "Budget"
    assert 0.70 <= payload["confidence"] <= 0.80
    assert payload["model"] == "Random Forest"


def test_predict_unknown_neighbourhood_returns_404():
    response = client.post("/api/predict", json={"neighbourhood": "Not A Real Place"})
    assert response.status_code == 404
    assert "Unknown neighbourhood" in response.json()["detail"]


def test_get_neighbourhood_detail_known():
    response = client.get("/api/neighbourhood/Agincourt North")
    assert response.status_code == 200
    payload = response.json()

    assert payload["neighbourhood"] == "Agincourt North"
    assert payload["cluster_label"] == "Connected Family Neighborhood"
    assert payload["cluster_id"] == 1
    assert payload["profile"]["YEAR"] == 2024
    assert payload["prediction"]["predicted_tier"] == 1
    assert payload["prediction"]["tier_label"] == "Budget"


def test_get_clusters_shape_and_counts():
    response = client.get("/api/clusters")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 7

    counts = {row["cluster_id"]: row["count"] for row in payload}
    assert counts == {0: 22, 1: 45, 2: 56, 3: 5, 4: 2, 5: 18, 6: 10}


def test_get_affordable_for_80k_income():
    response = client.get("/api/affordable", params={"income": 80000})
    assert response.status_code == 200
    payload = response.json()

    assert payload["annual_income"] == 80000.0
    assert payload["monthly_budget"] == 2000.0
    assert len(payload["neighbourhoods"]) == 3

    names = {item["neighbourhood"] for item in payload["neighbourhoods"]}
    assert names == {
        "Humber Heights-Westmount",
        "Kingsview Village-The Westway",
        "Willowridge-Martingrove-Richview",
    }
