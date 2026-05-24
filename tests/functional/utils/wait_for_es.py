import time

from elasticsearch import Elasticsearch

from settings import test_settings

if __name__ == '__main__':
    es_client = Elasticsearch(hosts=test_settings.es_host, verify_certs=False)
    while True:
        if es_client.ping():
            break
        time.sleep(1)
