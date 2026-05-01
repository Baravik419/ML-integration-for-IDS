import time

from elastic_fetcher import fetch_recent_flows_without_alert, write_ml_result
from feature_mapper import map_suricata_flow_to_features
from inference_engine import load_model, predict_one, build_ml_result_doc

POLL_INTERVAL_SECONDS = 10
FETCH_BATCH_SIZE = 20

def get_flow_unique_id(doc: dict) -> str:
    suricata_eve = doc.get("suricata", {}).get("eve", {})
    flow_id = suricata_eve.get("flow_id", "unknown")
    timestamp = doc.get("@timestamp", "unknown")
    src_ip = doc.get("source", {}).get("ip", "unknown")
    dst_ip = doc.get("destination", {}).get("ip", "unknown")

    return f"{flow_id}|{timestamp}|{src_ip}|{dst_ip}"


def run_ml_service():
    print("Loading integration model...")
    model = load_model("Models/XGBoost_Model_Integration (5 fold)/XGBoost_Model_Integration.pkl")
    print("Model loaded. Starting service loop...")

    processed_flow_ids = set()

    while True:
        try:
            docs = fetch_recent_flows_without_alert(size=FETCH_BATCH_SIZE)
            docs = list(reversed(docs))

            for doc in docs:
                unique_id = get_flow_unique_id(doc)

                if unique_id in processed_flow_ids:
                    continue

                mapped_features = map_suricata_flow_to_features(doc)
                prediction = predict_one(model, mapped_features)
                result_doc = build_ml_result_doc(doc, mapped_features, prediction)

                response = write_ml_result(result_doc)

                print(f"Processed flow: {unique_id}")
                print(f"Prediction: {prediction}")
                print(f"Elasticsearch result: {response['result']}")

                processed_flow_ids.add(unique_id)

            if len(processed_flow_ids) > 5000:
                processed_flow_ids = set(list(processed_flow_ids)[-2000:])

        except Exception as error:
            print(f"Service error: {error}")

        time.sleep(POLL_INTERVAL_SECONDS)

if __name__ == "__main__":
    run_ml_service()