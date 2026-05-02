import ml_service

def test_get_flow_unique_id_returns_expected_id():
    doc = {
        "@timestamp": "2004-01-19T16:33:26.000Z",
        "source": {
            "ip": "192.168.50.10"
        },
        "destination": {
            "ip": "8.8.8.8"
        },
        "suricata": {
            "eve": {
                "flow_id": 12345
            }
        }
    }

    result = ml_service.get_flow_unique_id(doc)

    assert result == "12345|2004-01-19T16:33:26.000Z|192.168.50.10|8.8.8.8"

def test_get_flow_unique_id_uses_unknown_when_fields_are_missing():
    doc = {}

    result = ml_service.get_flow_unique_id(doc)

    assert result == "unknown|unknown|unknown|unknown"

def test_run_ml_service_processes_one_flow(monkeypatch):
    doc = {
        "@timestamp": "2004-01-19T16:33:26.000Z",
        "source": {"ip": "192.168.50.10"},
        "destination": {"ip": "8.8.8.8"},
        "suricata": {
            "eve": {
                "flow_id": 12345
            }
        }
    }

    written_docs = []

    monkeypatch.setattr(ml_service, "load_model", lambda path: "fake_model")

    monkeypatch.setattr(
        ml_service,
        "fetch_recent_flows_without_alert",
        lambda size: [doc]
    )

    monkeypatch.setattr(
        ml_service,
        "map_suricata_flow_to_features",
        lambda input_doc: {
            "src_ip": "192.168.50.10",
            "dst_ip": "8.8.8.8",
            "proto": "udp"
        }
    )

    monkeypatch.setattr(
        ml_service,
        "predict_one",
        lambda model, features: {
            "predicted_class": "ddos",
            "confidence": 95.0
        }
    )

    monkeypatch.setattr(
        ml_service,
        "build_ml_result_doc",
        lambda source_doc, mapped_features, prediction: {
            "@timestamp": "2004-01-19T16:33:26.000Z",
            "event_type": "alert",
            "ml": prediction
        }
    )

    def fake_write_ml_result(result_doc):
        written_docs.append(result_doc)
        return {"result": "created"}

    monkeypatch.setattr(ml_service, "write_ml_result", fake_write_ml_result)

    def stop_after_one_loop(seconds):
        raise KeyboardInterrupt

    monkeypatch.setattr(ml_service.time, "sleep", stop_after_one_loop)

    try:
        ml_service.run_ml_service()
    except KeyboardInterrupt:
        pass

    assert len(written_docs) == 1
    assert written_docs[0]["event_type"] == "alert"
    assert written_docs[0]["ml"]["predicted_class"] == "ddos"
    assert written_docs[0]["ml"]["confidence"] == 95.0

