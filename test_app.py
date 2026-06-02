import json

import pytest

from app import app
from calculator import calculate_grade, calculate_stats


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


class TestCalculateGrade:
    def test_hd_boundary(self):
        result = calculate_grade(85)
        assert result["grade"] == "HD"
        assert result["gpa"] == 4.0

    def test_hd_high(self):
        result = calculate_grade(100)
        assert result["grade"] == "HD"

    def test_distinction_boundary(self):
        result = calculate_grade(75)
        assert result["grade"] == "D"
        assert result["gpa"] == 3.0

    def test_distinction_mid(self):
        result = calculate_grade(80)
        assert result["grade"] == "D"

    def test_credit_boundary(self):
        result = calculate_grade(65)
        assert result["grade"] == "C"
        assert result["gpa"] == 2.0

    def test_pass_boundary(self):
        result = calculate_grade(50)
        assert result["grade"] == "P"
        assert result["gpa"] == 1.0

    def test_fail_boundary(self):
        result = calculate_grade(49)
        assert result["grade"] == "N"
        assert result["gpa"] == 0.0

    def test_fail_zero(self):
        result = calculate_grade(0)
        assert result["grade"] == "N"

    def test_invalid_above_100(self):
        with pytest.raises(ValueError):
            calculate_grade(101)

    def test_invalid_negative(self):
        with pytest.raises(ValueError):
            calculate_grade(-1)

    def test_invalid_type_string(self):
        with pytest.raises(TypeError):
            calculate_grade("high")

    def test_float_mark(self):
        result = calculate_grade(84.9)
        assert result["grade"] == "D"


class TestCalculateStats:
    def test_basic_stats(self):
        stats = calculate_stats([50, 75, 85, 100])
        assert stats["count"] == 4
        assert stats["average"] == 77.5
        assert stats["highest"] == 100
        assert stats["lowest"] == 50

    def test_pass_rate_all_pass(self):
        stats = calculate_stats([50, 60, 70, 80])
        assert stats["pass_rate"] == 100.0

    def test_pass_rate_mixed(self):
        stats = calculate_stats([40, 50])
        assert stats["pass_rate"] == 50.0

    def test_empty_list(self):
        stats = calculate_stats([])
        assert stats == {}

    def test_single_mark(self):
        stats = calculate_stats([72])
        assert stats["count"] == 1
        assert stats["average"] == 72.0


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_status(self, client):
        response = client.get("/health")
        data = json.loads(response.data)
        assert data["status"] == "healthy"
        assert data["service"] == "grade-api"


class TestGradeEndpoint:
    def test_single_mark(self, client):
        response = client.post(
            "/grade",
            data=json.dumps({"marks": [85]}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["results"][0]["grade"] == "HD"

    def test_multiple_marks(self, client):
        response = client.post(
            "/grade",
            data=json.dumps({"marks": [40, 55, 70, 85, 95]}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data["results"]) == 5

    def test_missing_marks_field(self, client):
        response = client.post(
            "/grade",
            data=json.dumps({"score": [85]}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_empty_marks_list(self, client):
        response = client.post(
            "/grade",
            data=json.dumps({"marks": []}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_invalid_mark_returns_500_for_monitoring_demo(self, client):
        response = client.post(
            "/grade",
            data=json.dumps({"marks": [101]}),
            content_type="application/json",
        )
        assert response.status_code == 500

    def test_no_body(self, client):
        response = client.post("/grade", content_type="application/json")
        assert response.status_code == 400

    def test_stats_included(self, client):
        response = client.post(
            "/grade",
            data=json.dumps({"marks": [60, 80]}),
            content_type="application/json",
        )
        data = json.loads(response.data)
        assert "stats" in data
        assert data["stats"]["average"] == 70.0


class TestBatchEndpoint:
    def test_batch_grades(self, client):
        payload = {
            "students": [
                {"name": "Alice", "marks": [85, 90]},
                {"name": "Bob", "marks": [45, 55]},
            ]
        }
        response = client.post(
            "/grades/batch",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data["students"]) == 2
        assert data["students"][0]["name"] == "Alice"

    def test_batch_missing_field(self, client):
        response = client.post(
            "/grades/batch",
            data=json.dumps({"data": []}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_batch_empty_student_marks(self, client):
        response = client.post(
            "/grades/batch",
            data=json.dumps({"students": [{"name": "No Marks", "marks": []}]}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["students"][0]["stats"] == {}


class TestMetricsEndpoint:
    def test_metrics_returns_200(self, client):
        response = client.get("/metrics")
        assert response.status_code == 200

    def test_metrics_content_type(self, client):
        response = client.get("/metrics")
        assert (
            b"app_request_count_total" in response.data
            or b"grade_calculation_total" in response.data
        )
