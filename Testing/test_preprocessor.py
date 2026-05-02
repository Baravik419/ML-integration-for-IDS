import pytest
import pandas as pd
import preprocessor
from preprocessor import features_to_dataframe
from preprocessor import encode_categorical_columns
from preprocessor import scale_features

def test_load_model_data_loads_all_required_files(monkeypatch):
    loaded_paths = []

    def fake_joblib_load(path):
        loaded_paths.append(path)

        if path.endswith("XGB_Integration_X_columns.pkl"):
            return ["src_ip", "dst_ip", "proto"]

        if path.endswith("XGB_Integration_scaler.pkl"):
            return "fake_scaler"

        if path.endswith("XGB_Integration_Ordinal_Encoder.pkl"):
            return "fake_encoder"

    monkeypatch.setattr(preprocessor.joblib, "load", fake_joblib_load)

    x_columns, scaler, ordinal_encoder = preprocessor.load_model_data()

    assert x_columns == ["src_ip", "dst_ip", "proto"]
    assert scaler == "fake_scaler"
    assert ordinal_encoder == "fake_encoder"

    assert len(loaded_paths) == 3
    assert loaded_paths[0].endswith("XGB_Integration_X_columns.pkl")
    assert loaded_paths[1].endswith("XGB_Integration_scaler.pkl")
    assert loaded_paths[2].endswith("XGB_Integration_Ordinal_Encoder.pkl")

def test_load_model_data_raises_error_when_file_loading_fails(monkeypatch):
    def fake_joblib_load(path):
        if path.endswith("XGB_Integration_scaler.pkl"):
            raise FileNotFoundError("Scaler file not found")

        if path.endswith("XGB_Integration_X_columns.pkl"):
            return ["src_ip", "dst_ip", "proto"]

        if path.endswith("XGB_Integration_Ordinal_Encoder.pkl"):
            return "fake_encoder"

    monkeypatch.setattr(preprocessor.joblib, "load", fake_joblib_load)

    with pytest.raises(FileNotFoundError) as error:
        preprocessor.load_model_data()

    assert str(error.value) == "Scaler file not found"

def test_features_to_dataframe_keeps_columns_in_model_order():
    features = {
        "proto": "udp",
        "src_ip": "192.168.50.10",
        "dst_ip": "8.8.8.8"
    }

    x_columns = ["src_ip", "dst_ip", "proto"]

    result = features_to_dataframe(features, x_columns)

    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == ["src_ip", "dst_ip", "proto"]
    assert result.loc[0, "src_ip"] == "192.168.50.10"
    assert result.loc[0, "dst_ip"] == "8.8.8.8"
    assert result.loc[0, "proto"] == "udp"

def test_features_to_dataframe_adds_missing_columns_with_zero():
    features = {
        "src_ip": "192.168.50.10"
    }

    x_columns = ["src_ip", "dst_ip", "proto", "src_port"]

    result = features_to_dataframe(features, x_columns)

    assert list(result.columns) == ["src_ip", "dst_ip", "proto", "src_port"]
    assert result.loc[0, "src_ip"] == "192.168.50.10"
    assert result.loc[0, "dst_ip"] == 0
    assert result.loc[0, "proto"] == 0
    assert result.loc[0, "src_port"] == 0

def test_encode_categorical_columns_transforms_only_categorical_columns():
    features = {
        "src_ip": "192.168.50.10",
        "dst_ip": "8.8.8.8",
        "proto": "udp",
        "service": "dns",
        "conn_state": "SF",
        "src_port": 51514,
        "dst_port": 53
    }

    df = pd.DataFrame([features])

    class FakeOrdinalEncoder:
        def transform(self, categorical_df):
            assert list(categorical_df.columns) == [
                "src_ip",
                "dst_ip",
                "proto",
                "service",
                "conn_state"
            ]

            return [[1, 2, 3, 4, 5]]

    result = encode_categorical_columns(df, FakeOrdinalEncoder())

    assert result.loc[0, "src_ip"] == 1
    assert result.loc[0, "dst_ip"] == 2
    assert result.loc[0, "proto"] == 3
    assert result.loc[0, "service"] == 4
    assert result.loc[0, "conn_state"] == 5

    assert result.loc[0, "src_port"] == 51514
    assert result.loc[0, "dst_port"] == 53

def test_encode_categorical_columns_does_not_modify_original_dataframe():
    features = {
        "src_ip": "192.168.50.10",
        "dst_ip": "8.8.8.8",
        "proto": "udp",
        "service": "dns",
        "conn_state": "SF",
        "src_port": 51514
    }

    df = pd.DataFrame([features])

    class FakeOrdinalEncoder:
        def transform(self, categorical_df):
            return [[1, 2, 3, 4, 5]]

    result = encode_categorical_columns(df, FakeOrdinalEncoder())

    assert result.loc[0, "src_ip"] == 1
    assert df.loc[0, "src_ip"] == "192.168.50.10"
    assert df.loc[0, "proto"] == "udp"

def test_scale_features_returns_dataframe_with_same_columns_and_index():
    df = pd.DataFrame(
        [
            {
                "src_port": 51514,
                "dst_port": 53,
                "duration": 1000
            }
        ],
        index=[7]
    )

    class FakeScaler:
        def transform(self, input_df):
            assert list(input_df.columns) == ["src_port", "dst_port", "duration"]
            assert list(input_df.index) == [7]

            return [[0.1, 0.2, 0.3]]

    result = scale_features(df, FakeScaler())

    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == ["src_port", "dst_port", "duration"]
    assert list(result.index) == [7]
    assert result.loc[7, "src_port"] == 0.1
    assert result.loc[7, "dst_port"] == 0.2
    assert result.loc[7, "duration"] == 0.3

def test_scale_features_handles_multiple_rows():
    df = pd.DataFrame(
        [
            {"src_port": 1000, "dst_port": 80},
            {"src_port": 2000, "dst_port": 443}
        ]
    )

    class FakeScaler:
        def transform(self, input_df):
            assert len(input_df) == 2
            assert list(input_df.columns) == ["src_port", "dst_port"]

            return [
                [0.1, 0.2],
                [0.3, 0.4]
            ]

    result = scale_features(df, FakeScaler())

    assert list(result.columns) == ["src_port", "dst_port"]
    assert len(result) == 2
    assert result.loc[0, "src_port"] == 0.1
    assert result.loc[0, "dst_port"] == 0.2
    assert result.loc[1, "src_port"] == 0.3
    assert result.loc[1, "dst_port"] == 0.4

def test_prepare_features_for_inference_runs_full_pipeline(monkeypatch):
    features = {
        "src_ip": "192.168.50.10",
        "dst_ip": "8.8.8.8",
        "proto": "udp",
        "service": "dns",
        "conn_state": "SF",
        "src_port": 51514
    }

    class FakeOrdinalEncoder:
        def transform(self, categorical_df):
            return [[1, 2, 3, 4, 5]]

    class FakeScaler:
        def transform(self, df):
            return [[0.1, 0.2, 0.3, 0.4, 0.5, 0.6]]

    def fake_load_model_data():
        return (
            ["src_ip", "dst_ip", "proto", "service", "conn_state", "src_port"],
            FakeScaler(),
            FakeOrdinalEncoder()
        )

    monkeypatch.setattr(preprocessor, "load_model_data", fake_load_model_data)

    result = preprocessor.prepare_features_for_inference(features)

    assert list(result.columns) == [
        "src_ip",
        "dst_ip",
        "proto",
        "service",
        "conn_state",
        "src_port"
    ]

    assert result.loc[0, "src_ip"] == 0.1
    assert result.loc[0, "dst_ip"] == 0.2
    assert result.loc[0, "proto"] == 0.3
    assert result.loc[0, "service"] == 0.4
    assert result.loc[0, "conn_state"] == 0.5
    assert result.loc[0, "src_port"] == 0.6

def test_prepare_features_for_inference_ignores_extra_feature_fields(monkeypatch):
    features = {
        "src_ip": "192.168.50.10",
        "dst_ip": "8.8.8.8",
        "proto": "udp",
        "service": "dns",
        "conn_state": "SF",
        "src_port": 51514,
        "extra_field": "should_be_ignored"
    }

    class FakeOrdinalEncoder:
        def transform(self, categorical_df):
            assert "extra_field" not in categorical_df.columns
            return [[1, 2, 3, 4, 5]]

    class FakeScaler:
        def transform(self, df):
            assert "extra_field" not in df.columns
            return [[0.1, 0.2, 0.3, 0.4, 0.5, 0.6]]

    def fake_load_model_data():
        return (
            ["src_ip", "dst_ip", "proto", "service", "conn_state", "src_port"],
            FakeScaler(),
            FakeOrdinalEncoder()
        )

    monkeypatch.setattr(preprocessor, "load_model_data", fake_load_model_data)

    result = preprocessor.prepare_features_for_inference(features)

    assert "extra_field" not in result.columns
    assert list(result.columns) == [
        "src_ip",
        "dst_ip",
        "proto",
        "service",
        "conn_state",
        "src_port"
    ]