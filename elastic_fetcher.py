from elasticsearch import Elasticsearch
from getpass import getpass

def get_es_client():
    password = getpass("Enter Elasticsearch password: ")

    return Elasticsearch(
        "https://127.0.0.1:9200",
        basic_auth=("elastic", password),
        verify_certs=False
    )

def fetch_latest_flow_without_alert():
    elasticsearch = get_es_client()

    query = {
        "size": 1,
        "query": {
            "bool": {
                "must": [
                    {"term": {"suricata.eve.event_type": "flow"}},
                    {"term": {"suricata.eve.flow.alerted": False}}
                ]
            }
        },
        "sort": [
            {"@timestamp": {"order": "desc"}}
        ]
    }

    response = elasticsearch.search(index="filebeat-*", body=query)
    hits = response["hits"]["hits"]

    if not hits:
        return None

    return hits[0]["_source"]

def write_ml_result(result_doc: dict):
    elasticsearch = get_es_client()
    response = elasticsearch.index(index="filebeat-9.3.3", document=result_doc)
    return response

def build_ml_result_doc(source_doc: dict, mapped_features: dict, prediction: dict) -> dict:
    return {
        "@timestamp": source_doc["@timestamp"],

        #EVE style
        "timestamp": source_doc["@timestamp"],
        "event_type": "alert",
        "src_ip": mapped_features.get("src_ip"),
        "src_port": mapped_features.get("src_port"),
        "dest_ip": mapped_features.get("dst_ip"),
        "dest_port": mapped_features.get("dst_port"),
        "proto": mapped_features.get("proto"),

        "alert": {
            "signature": f"ML prediction: {prediction['predicted_class']}",
            "signature_id": 9000001,
            "category": "ML IDS Prediction",
            "severity": 2
        },

        #ECS style
        "suricata": {
            "eve": {
                "event_type": "alert",
                "in_iface": source_doc.get("suricata", {}).get("eve", {}).get("in_iface", "ens18"),
                "alert": {
                    "signature_id": 9000001,
                    "signature": f"ML prediction: {prediction['predicted_class']}",
                    "category": "ML IDS Prediction"
                }
            }
        },

        "event": {
            "kind": "alert",
            "module": "ml_ids",
            "dataset": "ml.suricata",
            "severity": 2,
            "category": ["network", "intrusion_detection"],
            "type": ["info"]
        },

        "ml": {
            "predicted_class": prediction["predicted_class"],
            "confidence": prediction["confidence"],
        },

        "source":{
            "ip": mapped_features.get("src_ip"),
            "port": mapped_features.get("src_port"),
        },

        "destination":{
            "ip": mapped_features.get("dst_ip"),
            "port": mapped_features.get("dst_port"),
        },

        "network":{
            "transport": mapped_features.get("proto"),
        },

        "suricata": {
            "flow":{
                "state": mapped_features.get("conn_state"),
            }
        },

        "related": {
          "ip": [
              mapped_features.get("src_ip"),
              mapped_features.get("dst_ip"),
          ]
        }
    }