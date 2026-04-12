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