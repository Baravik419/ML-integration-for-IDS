import json
from datetime import datetime

# Transforming suricata ts format to the model's ts format
def sur_timestamp_to_unix_ms(ts: str) -> int:
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return int(dt.timestamp() * 1000)

# Parsing the event original field
def parse_event_original(event_original: str) -> dict:
    if not event_original:
        return {}

    try:
        return json.loads(event_original)
    except Exception:
        return {}

#Mapping features
def map_suricata_flow_to_features(doc: dict) -> dict:
    source = doc.get("source", {})
    destination = doc.get("destination", {})
    network = doc.get("network", {})
    suricata = doc.get("suricata", {}).get("eve", {})
    event = doc.get("event", {})
    flow = suricata.get("flow", {})
    original = parse_event_original(event.get("original"))
    proto = network.get("transport") or original.get("proto", "").lower()
    service = network.get("protocol") or original.get("app_proto", "unknown").lower()

    features = {
        "ts": sur_timestamp_to_unix_ms(doc["@timestamp"]),
        "src_ip": source.get("ip"),
        "src_port": source.get("port", 0),
        "dst_ip": destination.get("ip"),
        "dst_port": destination.get("port", 0),
        "proto": proto,
        "service": service,
        "duration": event.get("duration", 0),
        "src_bytes": source.get("bytes", 0),
        "dst_bytes": destination.get("bytes", 0),
        "src_pkts": source.get("packets", 0),
        "dst_pkts": destination.get("packets", 0),
        "conn_state": flow.get("state", "unknown"),
    }

    return features

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

    mapped = map_suricata_flow_to_features(sample_doc)
    print(mapped)