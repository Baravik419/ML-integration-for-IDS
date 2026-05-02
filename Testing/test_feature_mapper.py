from feature_mapper import sur_timestamp_to_unix_ms
from feature_mapper import parse_event_original
from feature_mapper import map_suricata_flow_to_features

def test_sur_timestamp_to_unix_ms():
    timestamp = "2004-01-19T16:33:26.000Z"

    result = sur_timestamp_to_unix_ms(timestamp)

    assert result == 1074530006000

def test_parse_event_original_valid_json():
    event_original = '{"proto": "TCP", "app_proto": "http"}'

    result = parse_event_original(event_original)

    assert result["proto"] == "TCP"
    assert result["app_proto"] == "http"

def test_parse_event_original_invalid_json():
    event_original = "{bad json"

    result = parse_event_original(event_original)

    assert result == {}

def test_map_suricata_flow_to_features_normal_flow():
    doc = {
        "@timestamp": "2004-01-19T16:33:26Z",
        "source": {
            "ip": "192.168.50.10",
            "port": 51514,
            "bytes": 500,
            "packets": 5
        },
        "destination": {
            "ip": "8.8.8.8",
            "port": 53,
            "bytes": 1200,
            "packets": 8
        },
        "network": {
            "transport": "udp",
            "protocol": "dns"
        },
        "event": {
            "duration": 1000000
        },
        "suricata": {
            "eve": {
                "flow": {
                    "state": "established"
                }
            }
        }
    }

    result = map_suricata_flow_to_features(doc)

    assert result["src_ip"] == "192.168.50.10"
    assert result["src_port"] == 51514
    assert result["dst_ip"] == "8.8.8.8"
    assert result["dst_port"] == 53
    assert result["proto"] == "udp"
    assert result["service"] == "dns"
    assert result["src_bytes"] == 500
    assert result["dst_bytes"] == 1200
    assert result["src_pkts"] == 5
    assert result["dst_pkts"] == 8
    assert result["conn_state"] == "established"

def test_map_suricata_flow_to_features_with_missing_fields():
    doc = {
        "@timestamp": "2026-05-02T12:00:00Z",
        "event": {
            "original": '{"proto": "TCP", "app_proto": "http"}'
        }
    }

    result = map_suricata_flow_to_features(doc)

    assert result["src_ip"] is None
    assert result["src_port"] == 0
    assert result["dst_ip"] is None
    assert result["dst_port"] == 0
    assert result["proto"] == "tcp"
    assert result["service"] == "http"
    assert result["duration"] == 0
    assert result["src_bytes"] == 0
    assert result["dst_bytes"] == 0
    assert result["src_pkts"] == 0
    assert result["dst_pkts"] == 0
    assert result["conn_state"] == "unknown"
