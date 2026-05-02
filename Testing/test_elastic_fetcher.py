import pytest
from elasticsearch import Elasticsearch
import elastic_fetcher
from elastic_fetcher import get_es_client

def test_get_es_client_raises_error_if_password_is_not_set(monkeypatch):
    monkeypatch.delenv("ES_PASSWORD", raising=False)

    with pytest.raises(ValueError) as error:
        get_es_client()

    assert str(error.value) == "ES_PASSWORD environment variable is not set"

def test_get_es_client_returns_es_client_when_password_exists(monkeypatch):
    monkeypatch.setenv("ES_PASSWORD", "test_password")

    client = get_es_client()

    assert isinstance(client, Elasticsearch)

def test_fetch_latest_flow_without_alert_returns_none_when_no_hits(monkeypatch):
    class FakeElasticsearch:
        def search(self, index, body):
            return {
                "hits": {
                    "hits": []
                }
            }

    monkeypatch.setattr(elastic_fetcher, "get_es_client", lambda: FakeElasticsearch())

    result = elastic_fetcher.fetch_latest_flow_without_alert()

    assert result is None

def test_fetch_latest_flow_without_alert_returns_latest_flow(monkeypatch):
    class FakeElasticsearch:
        def search(self, index, body):
            assert index == "filebeat-*"
            assert body["size"] == 1
            assert body["query"]["bool"]["must"][0]["term"]["suricata.eve.event_type"] == "flow"
            assert body["query"]["bool"]["must"][1]["term"]["suricata.eve.flow.alerted"] is False
            assert body["sort"][0]["@timestamp"]["order"] == "desc"

            return {
                "hits": {
                    "hits": [
                        {
                            "_source": {
                                "@timestamp": "2004-01-19T16:33:26.000Z",
                                "source": {"ip": "192.168.50.10"}
                            }
                        }
                    ]
                }
            }

    monkeypatch.setattr(elastic_fetcher, "get_es_client", lambda: FakeElasticsearch())

    result = elastic_fetcher.fetch_latest_flow_without_alert()

    assert result["@timestamp"] == "2004-01-19T16:33:26.000Z"
    assert result["source"]["ip"] == "192.168.50.10"

def test_write_ml_result_indexes_document(monkeypatch):
    result_doc = {
        "@timestamp": "2004-01-19T16:33:26.000Z",
        "event_type": "alert",
        "ml": {
            "predicted_class": "ddos",
            "confidence": 95.0
        }
    }

    class FakeElasticsearch:
        def index(self, index, document):
            assert index == "filebeat-9.3.3"
            assert document == result_doc

            return {
                "result": "created"
            }

    monkeypatch.setattr(elastic_fetcher, "get_es_client", lambda: FakeElasticsearch())

    response = elastic_fetcher.write_ml_result(result_doc)

    assert response["result"] == "created"

def test_write_ml_result_raises_error_when_index_fails(monkeypatch):
    result_doc = {
        "@timestamp": "2004-01-19T16:33:26.000Z",
        "event_type": "alert"
    }

    class FakeElasticsearch:
        def index(self, index, document):
            raise RuntimeError("Elasticsearch index failed")

    monkeypatch.setattr(elastic_fetcher, "get_es_client", lambda: FakeElasticsearch())

    with pytest.raises(RuntimeError) as error:
        elastic_fetcher.write_ml_result(result_doc)

    assert str(error.value) == "Elasticsearch index failed"

def test_build_ml_result_doc_creates_ml_alert():
    source_doc = {
        "@timestamp": "2004-01-19T16:33:26.000Z",
        "suricata": {
            "eve": {
                "in_iface": "ens19"
            }
        }
    }

    mapped_features = {
        "src_ip": "192.168.50.10",
        "src_port": 51514,
        "dst_ip": "8.8.8.8",
        "dst_port": 53,
        "proto": "udp"
    }

    prediction = {
        "predicted_class": "ddos",
        "confidence": 96.5
    }

    result = elastic_fetcher.build_ml_result_doc(
        source_doc,
        mapped_features,
        prediction
    )

    assert result["@timestamp"] == "2004-01-19T16:33:26.000Z"
    assert result["timestamp"] == "2004-01-19T16:33:26.000Z"

    assert result["event_type"] == "alert"
    assert result["event"]["kind"] == "alert"
    assert result["event"]["module"] == "ml_ids"

    assert result["alert"]["signature"] == "ML prediction: ddos"
    assert result["alert"]["signature_id"] == 9000001
    assert result["alert"]["category"] == "ML IDS Prediction"

    assert result["ml"]["predicted_class"] == "ddos"
    assert result["ml"]["confidence"] == 96.5

    assert result["source"]["ip"] == "192.168.50.10"
    assert result["source"]["port"] == 51514
    assert result["destination"]["ip"] == "8.8.8.8"
    assert result["destination"]["port"] == 53

    assert result["network"]["transport"] == "udp"
    assert result["suricata"]["eve"]["in_iface"] == "ens19"

def test_build_ml_result_doc_uses_default_interface_when_missing():
    source_doc = {
        "@timestamp": "2004-01-19T16:33:26.000Z",
        "suricata": {
            "eve": {}
        }
    }

    mapped_features = {
        "src_ip": "192.168.50.10",
        "src_port": 51514,
        "dst_ip": "8.8.8.8",
        "dst_port": 53,
        "proto": "udp"
    }

    prediction = {
        "predicted_class": "normal",
        "confidence": 88.0
    }

    result = elastic_fetcher.build_ml_result_doc(
        source_doc,
        mapped_features,
        prediction
    )

    assert result["suricata"]["eve"]["in_iface"] == "ens18"
    assert result["ml"]["predicted_class"] == "normal"
    assert result["alert"]["signature"] == "ML prediction: normal"