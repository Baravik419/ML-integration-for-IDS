import inference_engine
import pytest

def test_load_model_loads_model_from_given_path(monkeypatch):
    loaded_paths = []

    def fake_joblib_load(path):
        loaded_paths.append(path)
        return "fake_model"

    monkeypatch.setattr(inference_engine.joblib, "load", fake_joblib_load)

    result = inference_engine.load_model("Models/test_model.pkl")

    assert result == "fake_model"
    assert loaded_paths == ["Models/test_model.pkl"]

def test_load_model_raises_error_when_loading_fails(monkeypatch):
    def fake_joblib_load(path):
        raise FileNotFoundError("Model file not found")

    monkeypatch.setattr(inference_engine.joblib, "load", fake_joblib_load)

    with pytest.raises(FileNotFoundError) as error:
        inference_engine.load_model("Models/missing_model.pkl")

    assert str(error.value) == "Model file not found"

def test_predict_one_returns_predicted_class_and_confidence(monkeypatch):
    features = {
        "src_ip": "192.168.50.10",
        "dst_ip": "8.8.8.8",
        "proto": "udp"
    }

    def fake_prepare_features_for_inference(input_features):
        assert input_features == features
        return "fake_dataframe"

    class FakeLabelEncoder:
        def inverse_transform(self, values):
            assert values == [1]
            return ["ddos"]

    class FakeModel:
        def predict(self, df):
            assert df == "fake_dataframe"
            return [1]

        def predict_proba(self, df):
            assert df == "fake_dataframe"
            return [[0.05, 0.95, 0.00]]

    monkeypatch.setattr(
        inference_engine,
        "prepare_features_for_inference",
        fake_prepare_features_for_inference
    )

    monkeypatch.setattr(
        inference_engine,
        "load_label_encoder",
        lambda: FakeLabelEncoder()
    )

    result = inference_engine.predict_one(FakeModel(), features)

    assert result["predicted_class"] == "ddos"
    assert result["confidence"] == 95.0

def test_load_label_encoder_loads_encoder(monkeypatch):
    loaded_paths = []

    def fake_joblib_load(path):
        loaded_paths.append(path)
        return "fake_label_encoder"

    monkeypatch.setattr(inference_engine.joblib, "load", fake_joblib_load)

    result = inference_engine.load_label_encoder()

    assert result == "fake_label_encoder"
    assert len(loaded_paths) == 1
    assert loaded_paths[0].endswith("XGB_Integration_Label_Encoder.pkl")

def test_load_label_encoder_raises_error_when_loading_fails(monkeypatch):
    def fake_joblib_load(path):
        raise FileNotFoundError("Label encoder file not found")

    monkeypatch.setattr(inference_engine.joblib, "load", fake_joblib_load)

    with pytest.raises(FileNotFoundError) as error:
        inference_engine.load_label_encoder()

    assert str(error.value) == "Label encoder file not found"