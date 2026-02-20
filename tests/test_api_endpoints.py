"""
FastAPI API Endpoint 통합 테스트.

TestClient를 사용하여 backend/main.py의 모든 핵심 엔드포인트를 테스트합니다.
- GET /
- POST /api/health-check
- POST /api/analyze
- POST /api/continuous-metrics
- POST /api/bayesian-analysis
- POST /api/decision-memo
- POST /api/sequential-analysis
- GET /api/sequential-boundaries
"""

import io
import json
import math

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helper: CSV test data builders
# ---------------------------------------------------------------------------

def _make_csv_bytes(text: str) -> io.BytesIO:
    """Strip leading whitespace per line and encode to BytesIO."""
    lines = [line.strip() for line in text.strip().splitlines()]
    return io.BytesIO("\n".join(lines).encode("utf-8"))


def make_2variant_csv() -> io.BytesIO:
    """2-variant CSV with guardrail columns."""
    return _make_csv_bytes("""
        variant,users,conversions,guardrail_cancel,guardrail_error
        control,10000,1200,120,35
        treatment,10050,1320,118,33
    """)


def make_2variant_continuous_csv() -> io.BytesIO:
    """2-variant CSV with continuous metric columns (revenue)."""
    return _make_csv_bytes("""
        variant,users,conversions,revenue_sum,revenue_sum_sq
        control,5000,600,250000,15000000
        treatment,5100,660,280000,17000000
    """)


def make_multivariant_csv() -> io.BytesIO:
    """3-variant CSV (control + 2 treatments) with a guardrail column."""
    return _make_csv_bytes("""
        variant,users,conversions,guardrail_error
        control,10000,1200,35
        variant_a,9800,1300,40
        variant_b,10200,1150,32
    """)


def make_basic_csv() -> io.BytesIO:
    """Minimal 2-variant CSV without guardrail or continuous columns."""
    return _make_csv_bytes("""
        variant,users,conversions
        control,10000,1200
        treatment,10050,1320
    """)


# ---------------------------------------------------------------------------
# Helpers for uploading files via TestClient
# ---------------------------------------------------------------------------

def _upload_csv(endpoint: str, csv_fn, filename: str = "test.csv", **params):
    """POST a CSV file to *endpoint* and return the response."""
    buf = csv_fn()
    return client.post(
        endpoint,
        files={"file": (filename, buf, "text/csv")},
        params=params,
    )


def _assert_no_nan_inf(data, path=""):
    """Recursively assert that no value in the JSON tree is NaN or Infinity."""
    if isinstance(data, dict):
        for key, value in data.items():
            _assert_no_nan_inf(value, path=f"{path}.{key}")
    elif isinstance(data, list):
        for idx, value in enumerate(data):
            _assert_no_nan_inf(value, path=f"{path}[{idx}]")
    elif isinstance(data, float):
        assert not math.isnan(data), f"NaN found at {path}"
        assert not math.isinf(data), f"Inf found at {path}"


# ===================================================================
# 1. Root endpoint
# ===================================================================

class TestRootEndpoint:
    def test_root_returns_message(self):
        response = client.get("/")
        assert response.status_code == 200
        body = response.json()
        assert "message" in body
        assert "ExperimentOS" in body["message"]


# ===================================================================
# 2. POST /api/health-check
# ===================================================================

class TestHealthCheck:
    def test_health_check_success(self):
        """Valid 2-variant CSV returns status=success with expected keys."""
        response = _upload_csv("/api/health-check", make_2variant_csv)
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"

        result = body["result"]
        assert "overall_status" in result
        assert result["overall_status"] in ("Healthy", "Warning", "Blocked")
        assert "schema" in result
        assert "srm" in result

        assert "preview" in body
        assert isinstance(body["preview"], list)
        assert "columns" in body
        assert isinstance(body["columns"], list)
        assert "filename" in body

        _assert_no_nan_inf(body)

    def test_health_check_invalid_file(self):
        """Non-CSV file upload returns 400."""
        buf = io.BytesIO(b"this is not csv")
        response = client.post(
            "/api/health-check",
            files={"file": ("test.txt", buf, "text/plain")},
        )
        assert response.status_code == 400

    def test_health_check_multivariant(self):
        """3-variant CSV is accepted and produces a valid health-check."""
        response = _upload_csv("/api/health-check", make_multivariant_csv)
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["result"]["overall_status"] in ("Healthy", "Warning", "Blocked")

    def test_health_check_continuous_csv(self):
        """CSV with continuous metric columns also passes health-check."""
        response = _upload_csv("/api/health-check", make_2variant_continuous_csv)
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"


# ===================================================================
# 3. POST /api/analyze
# ===================================================================

class TestAnalyze:
    def test_analyze_2variant_success(self):
        """2-variant analysis returns expected result structure."""
        response = _upload_csv("/api/analyze", make_2variant_csv)
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["is_multivariant"] is False
        assert body["variant_count"] == 2

        primary = body["primary_result"]
        assert "p_value" in primary
        assert "absolute_lift" in primary
        assert "relative_lift" in primary
        assert "ci_95" in primary
        assert "is_significant" in primary
        assert "control" in primary
        assert "treatment" in primary

        assert isinstance(body["guardrail_results"], list)
        assert len(body["guardrail_results"]) > 0

        _assert_no_nan_inf(body)

    def test_analyze_multivariant_success(self):
        """Multi-variant analysis returns chi-square overall + per-variant results."""
        response = _upload_csv("/api/analyze", make_multivariant_csv)
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["is_multivariant"] is True
        assert body["variant_count"] == 3

        primary = body["primary_result"]
        assert primary.get("is_multivariant") is True
        assert "overall" in primary
        assert "variants" in primary
        assert isinstance(primary["variants"], dict)

        # Guardrails in multi-variant format
        guardrails = body["guardrail_results"]
        assert "by_variant" in guardrails

        _assert_no_nan_inf(body)

    def test_analyze_with_guardrails_param(self):
        """Passing guardrails= restricts guardrail analysis to specified columns."""
        response = _upload_csv(
            "/api/analyze",
            make_2variant_csv,
            guardrails="guardrail_cancel",
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"

        guardrail_names = [g["name"] for g in body["guardrail_results"]]
        assert "guardrail_cancel" in guardrail_names
        # guardrail_error should NOT be present because we filtered
        assert "guardrail_error" not in guardrail_names

    def test_analyze_invalid_csv(self):
        """Non-CSV file returns 400."""
        buf = io.BytesIO(b"not a csv at all")
        response = client.post(
            "/api/analyze",
            files={"file": ("data.txt", buf, "text/plain")},
        )
        assert response.status_code == 400

    def test_analyze_basic_csv_no_guardrails(self):
        """CSV with only variant/users/conversions produces empty guardrail list."""
        response = _upload_csv("/api/analyze", make_basic_csv)
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["guardrail_results"] == []


# ===================================================================
# 4. POST /api/continuous-metrics
# ===================================================================

class TestContinuousMetrics:
    def test_continuous_metrics_success(self):
        """CSV with _sum/_sum_sq columns returns continuous analysis results."""
        response = _upload_csv("/api/continuous-metrics", make_2variant_continuous_csv)
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["is_multivariant"] is False
        assert isinstance(body["continuous_results"], list)
        assert len(body["continuous_results"]) > 0

        # Each result should have metric_name and statistical fields
        first = body["continuous_results"][0]
        assert "metric_name" in first
        assert first["metric_name"] == "revenue"
        assert "is_valid" in first

        _assert_no_nan_inf(body)

    def test_continuous_no_metrics(self):
        """CSV without _sum columns returns empty continuous_results."""
        response = _upload_csv("/api/continuous-metrics", make_basic_csv)
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["continuous_results"] == [] or body["continuous_results"] == {"by_variant": {}}

    def test_continuous_metrics_invalid_file(self):
        """Non-CSV file returns 400."""
        buf = io.BytesIO(b"binary blob")
        response = client.post(
            "/api/continuous-metrics",
            files={"file": ("test.txt", buf, "text/plain")},
        )
        assert response.status_code == 400


# ===================================================================
# 5. POST /api/bayesian-analysis
# ===================================================================

class TestBayesianAnalysis:
    def test_bayesian_2variant(self):
        """2-variant Bayesian analysis returns prob_treatment_beats_control."""
        response = _upload_csv("/api/bayesian-analysis", make_2variant_csv)
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["is_multivariant"] is False

        conversion = body["bayesian_insights"]["conversion"]
        assert "prob_treatment_beats_control" in conversion
        prob = conversion["prob_treatment_beats_control"]
        assert 0.0 <= prob <= 1.0

        _assert_no_nan_inf(body)

    def test_bayesian_multivariant(self):
        """Multi-variant Bayesian analysis returns vs_control and prob_being_best."""
        response = _upload_csv("/api/bayesian-analysis", make_multivariant_csv)
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["is_multivariant"] is True

        conversion = body["bayesian_insights"]["conversion"]
        assert "vs_control" in conversion
        assert "prob_being_best" in conversion

        # prob_being_best should sum close to 1
        probs = conversion["prob_being_best"]
        assert isinstance(probs, dict)
        total = sum(probs.values())
        assert abs(total - 1.0) < 0.05  # allow small Monte Carlo noise

        _assert_no_nan_inf(body)

    def test_bayesian_invalid_file(self):
        """Non-CSV file returns 400."""
        buf = io.BytesIO(b"nope")
        response = client.post(
            "/api/bayesian-analysis",
            files={"file": ("bad.json", buf, "application/json")},
        )
        assert response.status_code == 400


# ===================================================================
# 6. POST /api/decision-memo
# ===================================================================

class TestDecisionMemo:
    @staticmethod
    def _make_healthy_health():
        return {
            "overall_status": "Healthy",
            "schema": {"status": "Healthy", "issues": ["검증 통과"]},
            "srm": {"status": "Healthy", "p_value": 0.75, "message": "SRM 정상"},
        }

    @staticmethod
    def _make_primary_significant():
        return {
            "control": {"users": 10000, "conversions": 1200, "rate": 0.12},
            "treatment": {"users": 10050, "conversions": 1320, "rate": 0.1313},
            "is_significant": True,
            "p_value": 0.001,
            "absolute_lift": 0.0113,
            "relative_lift": 0.094,
            "ci_95": [0.005, 0.018],
        }

    @staticmethod
    def _make_primary_not_significant():
        return {
            "control": {"users": 10000, "conversions": 1200, "rate": 0.12},
            "treatment": {"users": 10050, "conversions": 1230, "rate": 0.1224},
            "is_significant": False,
            "p_value": 0.15,
            "absolute_lift": 0.0024,
            "relative_lift": 0.020,
            "ci_95": [-0.002, 0.007],
        }

    @staticmethod
    def _make_clean_guardrails():
        return [
            {
                "name": "guardrail_cancel",
                "worsened": False,
                "severe": False,
                "delta": 0.0001,
                "control_rate": 0.012,
                "treatment_rate": 0.0121,
            },
        ]

    @staticmethod
    def _make_severe_guardrails():
        return [
            {
                "name": "guardrail_error",
                "worsened": True,
                "severe": True,
                "delta": 0.005,
                "control_rate": 0.01,
                "treatment_rate": 0.015,
            },
        ]

    def test_decision_memo_launch(self):
        """Significant primary + clean guardrails => Launch."""
        payload = {
            "experiment_name": "Test Launch Experiment",
            "health_result": self._make_healthy_health(),
            "primary_result": self._make_primary_significant(),
            "guardrail_results": self._make_clean_guardrails(),
        }
        response = client.post("/api/decision-memo", json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["decision"]["decision"] == "Launch"

        assert "memo_markdown" in body
        assert "Launch" in body["memo_markdown"]

        assert "memo_html" in body
        assert "<html>" in body["memo_html"]

        _assert_no_nan_inf(body)

    def test_decision_memo_hold_not_significant(self):
        """Non-significant primary => Hold."""
        payload = {
            "experiment_name": "Test Hold Experiment",
            "health_result": self._make_healthy_health(),
            "primary_result": self._make_primary_not_significant(),
            "guardrail_results": self._make_clean_guardrails(),
        }
        response = client.post("/api/decision-memo", json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body["decision"]["decision"] == "Hold"

    def test_decision_memo_rollback_severe_guardrail(self):
        """Significant primary + severe guardrail => Rollback."""
        payload = {
            "experiment_name": "Test Rollback Experiment",
            "health_result": self._make_healthy_health(),
            "primary_result": self._make_primary_significant(),
            "guardrail_results": self._make_severe_guardrails(),
        }
        response = client.post("/api/decision-memo", json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body["decision"]["decision"] == "Rollback"

    def test_decision_memo_blocked_health(self):
        """Blocked health status => Hold (data quality issue)."""
        blocked_health = {
            "overall_status": "Blocked",
            "schema": {
                "status": "Blocked",
                "issues": ["필수 컬럼 누락: conversions"],
            },
            "srm": None,
        }
        payload = {
            "experiment_name": "Blocked Health Experiment",
            "health_result": blocked_health,
            "primary_result": self._make_primary_significant(),
            "guardrail_results": self._make_clean_guardrails(),
        }
        response = client.post("/api/decision-memo", json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body["decision"]["decision"] == "Hold"

    def test_decision_memo_with_bayesian_insights(self):
        """Including optional bayesian_insights still produces a valid memo."""
        payload = {
            "experiment_name": "Bayesian Memo Test",
            "health_result": self._make_healthy_health(),
            "primary_result": self._make_primary_significant(),
            "guardrail_results": self._make_clean_guardrails(),
            "bayesian_insights": {
                "conversion": {
                    "prob_treatment_beats_control": 0.98,
                    "expected_loss": 0.0001,
                },
                "continuous": {},
            },
        }
        response = client.post("/api/decision-memo", json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body["decision"]["decision"] == "Launch"
        assert "Bayesian" in body["memo_markdown"]


# ===================================================================
# 7. POST /api/sequential-analysis
# ===================================================================

class TestSequentialAnalysis:
    def test_sequential_continue(self):
        """Early look with moderate effect should continue collecting data."""
        payload = {
            "control_users": 2000,
            "control_conversions": 200,
            "treatment_users": 2000,
            "treatment_conversions": 220,
            "target_sample_size": 20000,
            "current_look": 1,
            "max_looks": 5,
        }
        response = client.post("/api/sequential-analysis", json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"

        seq = body["sequential_result"]
        assert seq["can_stop"] is False
        assert seq["decision"] == "continue"
        assert seq["current_look"] == 1
        assert seq["max_looks"] == 5

        # Boundaries should be present for visualization
        assert "boundaries" in body
        assert isinstance(body["boundaries"], list)
        assert len(body["boundaries"]) == 5

        # Progress info
        assert "progress" in body
        assert body["progress"]["current_sample"] == 4000
        assert body["progress"]["target_sample"] == 20000

        _assert_no_nan_inf(body)

    def test_sequential_reject_large_effect(self):
        """Large effect at a later look should potentially reject the null."""
        payload = {
            "control_users": 9000,
            "control_conversions": 900,
            "treatment_users": 9000,
            "treatment_conversions": 1080,
            "target_sample_size": 20000,
            "current_look": 4,
            "max_looks": 5,
        }
        response = client.post("/api/sequential-analysis", json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"

        seq = body["sequential_result"]
        # With 2% absolute lift (10% vs 12%) at 90% info fraction,
        # this should cross the boundary
        assert seq["can_stop"] is True
        assert seq["decision"] == "reject_null"

        _assert_no_nan_inf(body)

    def test_sequential_invalid_look_zero(self):
        """current_look=0 should return 400 (ValueError from domain logic)."""
        payload = {
            "control_users": 1000,
            "control_conversions": 100,
            "treatment_users": 1000,
            "treatment_conversions": 110,
            "target_sample_size": 10000,
            "current_look": 0,
            "max_looks": 5,
        }
        response = client.post("/api/sequential-analysis", json=payload)
        assert response.status_code == 400

    def test_sequential_invalid_look_exceeds_max(self):
        """current_look > max_looks should return 400."""
        payload = {
            "control_users": 1000,
            "control_conversions": 100,
            "treatment_users": 1000,
            "treatment_conversions": 110,
            "target_sample_size": 10000,
            "current_look": 6,
            "max_looks": 5,
        }
        response = client.post("/api/sequential-analysis", json=payload)
        assert response.status_code == 400

    def test_sequential_final_look_fail_to_reject(self):
        """At the final look with a small effect, should fail_to_reject."""
        payload = {
            "control_users": 10000,
            "control_conversions": 1000,
            "treatment_users": 10000,
            "treatment_conversions": 1010,
            "target_sample_size": 20000,
            "current_look": 5,
            "max_looks": 5,
        }
        response = client.post("/api/sequential-analysis", json=payload)
        assert response.status_code == 200
        body = response.json()
        seq = body["sequential_result"]
        # Final look always sets can_stop=True
        assert seq["can_stop"] is True
        assert seq["decision"] == "fail_to_reject"

    def test_sequential_pocock_boundary(self):
        """Pocock boundary type is accepted and returns valid results."""
        payload = {
            "control_users": 2000,
            "control_conversions": 200,
            "treatment_users": 2000,
            "treatment_conversions": 220,
            "target_sample_size": 20000,
            "current_look": 1,
            "max_looks": 5,
            "boundary_type": "pocock",
        }
        response = client.post("/api/sequential-analysis", json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert len(body["boundaries"]) == 5

    def test_sequential_with_previous_looks(self):
        """Providing previous_looks is accepted and influences boundary calculation."""
        payload = {
            "control_users": 4000,
            "control_conversions": 400,
            "treatment_users": 4000,
            "treatment_conversions": 440,
            "target_sample_size": 20000,
            "current_look": 2,
            "max_looks": 5,
            "previous_looks": [
                {"look": 1, "info_fraction": 0.2},
            ],
        }
        response = client.post("/api/sequential-analysis", json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["sequential_result"]["current_look"] == 2


# ===================================================================
# 8. GET /api/sequential-boundaries
# ===================================================================

class TestSequentialBoundaries:
    def test_boundaries_default(self):
        """Default parameters return 5 OBF boundaries."""
        response = client.get("/api/sequential-boundaries")
        assert response.status_code == 200
        body = response.json()
        boundaries = body["boundaries"]
        assert isinstance(boundaries, list)
        assert len(boundaries) == 5

        for b in boundaries:
            assert "look" in b
            assert "z_boundary" in b
            assert "info_fraction" in b
            assert "alpha_spent" in b
            assert "cumulative_alpha" in b

        # OBF: boundaries should be decreasing (stricter early, lenient later)
        z_values = [b["z_boundary"] for b in boundaries]
        for i in range(1, len(z_values)):
            assert z_values[i] <= z_values[i - 1], (
                f"OBF z_boundary should be non-increasing: "
                f"look {i} ({z_values[i-1]:.3f}) > look {i+1} ({z_values[i]:.3f})"
            )

        _assert_no_nan_inf(body)

    def test_boundaries_pocock(self):
        """Pocock boundaries are more uniform than OBF."""
        response = client.get(
            "/api/sequential-boundaries",
            params={"boundary_type": "pocock"},
        )
        assert response.status_code == 200
        body = response.json()
        boundaries = body["boundaries"]
        assert len(boundaries) == 5

        z_values = [b["z_boundary"] for b in boundaries]

        # Pocock boundaries should be more uniform (smaller range) than OBF
        z_range = max(z_values) - min(z_values)
        # For Pocock with 5 looks, the range should be relatively small
        assert z_range < 1.0, f"Pocock boundary range too wide: {z_range:.3f}"

        _assert_no_nan_inf(body)

    def test_boundaries_custom_looks(self):
        """Custom max_looks=3 returns exactly 3 boundaries."""
        response = client.get(
            "/api/sequential-boundaries",
            params={"max_looks": 3},
        )
        assert response.status_code == 200
        body = response.json()
        assert len(body["boundaries"]) == 3

        # Config should reflect the request
        assert body["config"]["max_looks"] == 3
        assert body["config"]["boundary_type"] == "obrien_fleming"

    def test_boundaries_custom_alpha(self):
        """Custom alpha=0.01 produces higher z boundaries."""
        response_01 = client.get(
            "/api/sequential-boundaries",
            params={"alpha": 0.01},
        )
        response_05 = client.get("/api/sequential-boundaries")

        assert response_01.status_code == 200
        assert response_05.status_code == 200

        z_01 = [b["z_boundary"] for b in response_01.json()["boundaries"]]
        z_05 = [b["z_boundary"] for b in response_05.json()["boundaries"]]

        # More stringent alpha => higher z boundaries at each look
        for z1, z5 in zip(z_01, z_05):
            assert z1 >= z5, (
                f"alpha=0.01 boundary ({z1:.3f}) should be >= "
                f"alpha=0.05 boundary ({z5:.3f})"
            )

    def test_boundaries_single_look(self):
        """max_looks=1 returns exactly 1 boundary at info_fraction=1.0."""
        response = client.get(
            "/api/sequential-boundaries",
            params={"max_looks": 1},
        )
        assert response.status_code == 200
        body = response.json()
        assert len(body["boundaries"]) == 1
        assert body["boundaries"][0]["info_fraction"] == 1.0

    def test_boundaries_invalid_type(self):
        """Unknown boundary_type returns 400 or 500 with error detail."""
        response = client.get(
            "/api/sequential-boundaries",
            params={"boundary_type": "unknown_type"},
        )
        # The calculate_boundaries function raises ValueError for unknown types
        assert response.status_code in (400, 500)


# ===================================================================
# Cross-cutting: SafeJSONResponse NaN/Inf handling
# ===================================================================

class TestSafeJsonResponse:
    def test_nan_inf_sanitized_in_analysis(self):
        """Verify that JSON responses from /api/analyze contain no NaN/Inf."""
        response = _upload_csv("/api/analyze", make_2variant_csv)
        assert response.status_code == 200
        body = response.json()
        _assert_no_nan_inf(body)

    def test_nan_inf_sanitized_in_bayesian(self):
        """Verify that JSON responses from /api/bayesian-analysis contain no NaN/Inf."""
        response = _upload_csv("/api/bayesian-analysis", make_2variant_csv)
        assert response.status_code == 200
        body = response.json()
        _assert_no_nan_inf(body)

    def test_nan_inf_sanitized_in_continuous(self):
        """Verify that continuous metrics responses contain no NaN/Inf."""
        response = _upload_csv("/api/continuous-metrics", make_2variant_continuous_csv)
        assert response.status_code == 200
        body = response.json()
        _assert_no_nan_inf(body)

    def test_nan_inf_sanitized_in_sequential(self):
        """Verify that sequential analysis responses contain no NaN/Inf."""
        payload = {
            "control_users": 5000,
            "control_conversions": 500,
            "treatment_users": 5000,
            "treatment_conversions": 550,
            "target_sample_size": 20000,
            "current_look": 2,
            "max_looks": 5,
        }
        response = client.post("/api/sequential-analysis", json=payload)
        assert response.status_code == 200
        body = response.json()
        _assert_no_nan_inf(body)
