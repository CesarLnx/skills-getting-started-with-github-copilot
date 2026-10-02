import copy
from importlib import import_module

import pytest
from fastapi.testclient import TestClient


app_module = import_module("src.app")


@pytest.fixture
def client():
    return TestClient(app_module.app)


@pytest.fixture
def activities(monkeypatch):
    isolated_activities = copy.deepcopy(app_module.activities)
    monkeypatch.setattr(app_module, "activities", isolated_activities)
    return isolated_activities


def test_get_activities_returns_activity_data(client, activities):
    # Arrange
    expected_activities = activities

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_activities


def test_signup_adds_student_to_activity(client, activities):
    # Arrange
    activity_name = "Art Club"
    student_email = "student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": student_email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {student_email} for {activity_name}"
    }
    assert student_email in activities[activity_name]["participants"]


def test_signup_rejects_unknown_activity(client, activities):
    # Arrange
    activity_name = "Unknown Club"
    student_email = "student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": student_email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_rejects_duplicate_student(client, activities):
    # Arrange
    activity_name = "Art Club"
    student_email = "student@mergington.edu"
    activities[activity_name]["participants"].append(student_email)

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": student_email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Student already signed up"}
    assert activities[activity_name]["participants"].count(student_email) == 1


def test_unregister_removes_student_from_activity(client, activities):
    # Arrange
    activity_name = "Art Club"
    student_email = "student@mergington.edu"
    activities[activity_name]["participants"] = [
        student_email,
        student_email,
        "other@mergington.edu",
    ]

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": student_email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Removed {student_email} from {activity_name}"
    }
    assert activities[activity_name]["participants"] == ["other@mergington.edu"]


def test_unregister_rejects_unknown_activity(client, activities):
    # Arrange
    activity_name = "Unknown Club"
    student_email = "student@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": student_email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_rejects_student_not_signed_up(client, activities):
    # Arrange
    activity_name = "Art Club"
    student_email = "student@mergington.edu"
    original_participants = activities[activity_name]["participants"].copy()

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": student_email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Student is not signed up"}
    assert activities[activity_name]["participants"] == original_participants