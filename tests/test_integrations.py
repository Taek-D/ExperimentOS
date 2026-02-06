import pytest
import pandas as pd
from pydantic import ValidationError
from src.experimentos.integrations.schema import IntegrationResult, IntegrationVariant
from src.experimentos.integrations.transform import to_experiment_df

class TestIntegrationSchema:
    def test_valid_integration_result(self):
        result = IntegrationResult(
            experiment_id="exp_123",
            variants=[
                IntegrationVariant(name="control", users=1000, conversions=100),
                IntegrationVariant(name="treatment", users=1000, conversions=120)
            ]
        )
        assert result.experiment_id == "exp_123"
        assert len(result.variants) == 2

    def test_invalid_conversions_gt_users(self):
        with pytest.raises(ValidationError):
            IntegrationResult(
                experiment_id="exp_fail",
                variants=[
                    IntegrationVariant(name="A", users=100, conversions=150),
                    IntegrationVariant(name="B", users=100, conversions=50)
                ]
            )

    def test_unique_variant_names(self):
        with pytest.raises(ValidationError):
            IntegrationResult(
                experiment_id="exp_dup",
                variants=[
                    IntegrationVariant(name="A", users=100, conversions=10),
                    IntegrationVariant(name="A", users=100, conversions=10)
                ]
            )

class TestIntegrationTransform:
    def test_to_experiment_df_basic(self):
        result = IntegrationResult(
            experiment_id="test_df",
            variants=[
                IntegrationVariant(name="control", users=100, conversions=10),
                IntegrationVariant(name="treatment", users=100, conversions=15)
            ]
        )
        df = to_experiment_df(result)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "variant" in df.columns
        assert "users" in df.columns
        assert "conversions" in df.columns
        assert df.iloc[0]["variant"] == "control"
        assert df.iloc[0]["users"] == 100

    def test_to_experiment_df_with_metrics(self):
        result = IntegrationResult(
            experiment_id="test_metrics",
            variants=[
                IntegrationVariant(name="Control", users=100, conversions=10, metrics={"guardrail_A": 5}),
                IntegrationVariant(name="Treatment", users=100, conversions=12, metrics={"guardrail_A": 6})
            ]
        )
        df = to_experiment_df(result)
        
        # Check column normalization (Control -> control)
        assert "control" in df["variant"].values
        assert "treatment" in df["variant"].values # our transform standardizes 'Treatment' too
        
        # Check metrics
        assert "guardrail_A" in df.columns
        assert df[df["variant"] == "control"]["guardrail_A"].iloc[0] == 5.0

    def test_to_experiment_df_missing_metric_fill(self):
        """Test that missing metrics in one variant are filled (default 0)"""
        result = IntegrationResult(
            experiment_id="test_fill",
            variants=[
                IntegrationVariant(name="A", users=100, conversions=10, metrics={"only_in_a": 1}),
                IntegrationVariant(name="B", users=100, conversions=10, metrics={})
            ]
        )
        df = to_experiment_df(result)
        assert "only_in_a" in df.columns
        assert df[df["variant"] == "B"]["only_in_a"].iloc[0] == 0
