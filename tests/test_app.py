import src.app as app_module
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch):
    # Arrange shared, isolated activity data for each test.
    test_activities = {
        "Chess Club": {
            "description": "Learn chess",
            "schedule": "Fridays",
            "max_participants": 2,
            "participants": ["student@example.com"],
        },
        "Full Club": {
            "description": "A full activity",
            "schedule": "Mondays",
            "max_participants": 1,
            "participants": ["full@example.com"],
        },
    }
    monkeypatch.setattr(app_module, "activities", test_activities)

    with TestClient(app_module.app) as test_client:
        yield test_client


def test_get_activities_returns_activity_data(client):
    # Arrange
    expected_activity_names = {"Chess Club", "Full Club"}

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert set(response.json()) == expected_activity_names
    assert response.json()["Chess Club"]["participants"] == ["student@example.com"]


def test_signup_adds_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = "new@example.com"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )
    activities_response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in activities_response.json()[activity_name]["participants"]


def test_signup_rejects_duplicate_email_case_insensitively(client):
    # Arrange
    activity_name = "Chess Club"
    duplicate_email = " STUDENT@EXAMPLE.COM "

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": duplicate_email},
    )
    activities_response = client.get("/activities")

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert activities_response.json()[activity_name]["participants"] == ["student@example.com"]


def test_signup_rejects_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Club"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": "new@example.com"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_rejects_full_activity(client):
    # Arrange
    activity_name = "Full Club"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": "new@example.com"},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"


def test_unregister_removes_participant_case_insensitively(client):
    # Arrange
    activity_name = "Chess Club"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": " STUDENT@EXAMPLE.COM "},
    )
    activities_response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": "Unregistered STUDENT@EXAMPLE.COM from Chess Club"}
    assert activities_response.json()[activity_name]["participants"] == []


def test_unregister_rejects_missing_participant(client):
    # Arrange
    activity_name = "Chess Club"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": "missing@example.com"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_unregister_rejects_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Club"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": "student@example.com"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
