import joblib
from feature_mapper import map_suricata_flow_to_features
from elastic_fetcher import fetch_latest_flow_without_alert, write_ml_result, build_ml_result_doc
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
    doc = fetch_latest_flow_without_alert()

    if doc is None:
        print("No new flows without alert found.")
        exit(0)
    else:
        mapped_features = map_suricata_flow_to_features(doc)
        model = load_model("Models/XGBoost_Model_Integration (5 fold)/XGBoost_Model_Integration.pkl")
        prediction = predict_one(model, mapped_features)

        result_doc = build_ml_result_doc(doc, mapped_features, prediction)
        response = write_ml_result(result_doc)

        print(mapped_features)
        print(prediction)
        print(result)