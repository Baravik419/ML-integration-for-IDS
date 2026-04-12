import joblib
from feature_mapper import map_suricata_flow_to_features
from preprocessor import prepare_features_for_inference

def load_model(model_path: str):
    return joblib.load(model_path)

def predict_one(model, features: dict) -> dict:
    df = prepare_features_for_inference(features)
    label_encoder = load_label_encoder()

    predicted_class_index = model.predict(df)[0]
    probabilities = model.predict_proba(df)[0]
    confidence = max(probabilities)

    predicted_class = label_encoder.inverse_transform([predicted_class_index])[0]

    return {
        "predicted_class": predicted_class,
        "confidence": round(float(confidence) *100, 2)
    }

def load_label_encoder():
    return joblib.load("Models/XGBoost_Model_Integration (5 fold)/XGB_Integration_Label_Encoder.pkl")

if __name__ == "__main__":
    sample_doc = {
        "@timestamp": "2026-04-12T08:56:25.466Z",
        "source": {
            "ip": "192.168.1.56",
            "port": 57621,
            "bytes": 86,
            "packets": 1
        },
        "destination": {
            "ip": "192.168.1.255",
            "port": 57621,
            "bytes": 0,
            "packets": 0
        },
        "network": {
            "transport": "udp"
        },
        "event": {
            "duration": 0,
            "original": "{\"proto\":\"UDP\",\"app_proto\":\"failed\"}"
        },
        "suricata": {
            "eve": {
                "flow": {
                    "state": "new"
                }
            }
        }
    }

    mapped_features = map_suricata_flow_to_features(sample_doc)

    model = load_model("Models/XGBoost_Model_Integration (5 fold)/XGBoost_Model_Integration.pkl")
    result = predict_one(model, mapped_features)
    print(result)