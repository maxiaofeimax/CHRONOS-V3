import os
import json
import requests
import concurrent.futures
import logging
from typing import Dict, List
import time


def search(query_list: List[str], n_max_doc: int = 20, search_engine: str = 'google', freshness: str = '', read_page: bool = True) -> List[Dict[str, str]]:
    doc_lists = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(search_single, query, search_engine, freshness, read_page) for query in query_list]
        for future in concurrent.futures.as_completed(futures):
            try:
                doc_lists.append(future.result())
            except:
                pass
    doc_list = _rearrange_and_dedup([d for d in doc_lists if d])
    return doc_list[:n_max_doc]


def search_single(query: str, search_engine: str, freshness: str = '', read_page: bool = True) -> List[Dict[str, str]]:
    try:
        if search_engine == 'google':
            search_results = google(query, [],read_page)
            return format_results(search_results)
        else:
            search_results = local_request(query, search_engine)
            return local_format_results(search_results)
    except Exception as e:
        logging.error(f'Search failed: {str(e)}')
        raise ValueError(f'Search failed: {str(e)}')

def google(query, multi_query=[],read_pages=True):
    url = os.getenv("SEARCH_API_URL")
    headers = {"Authorization": 'Bearer ' + os.getenv("SEARCH_API_KEY"), "Content-Type": "application/json"}

    template = {
        "rid": "test",
        "scene": os.getenv("SEARCH_SCENE"),
        "uq": query,
        "debug": False,
        "fields": [],
        "page": 1,
        "rows": 10,
        "customConfigInfo": {
            "multiSearch": False,
            "qpMultiQueryConfig": multi_query,
            "qpMultiQuery": False,
            "qpMultiQueryHistory": [],
            "qpSpellcheck": False,
            "qpEmbedding": False,
            "knnWithScript": False,
            "rerankSize": 10,
            "qpTermsWeight": False,
            "qpToolPlan": False,
            "inspection": False,
            "readpage": read_pages,
            "readpageConfig": {"tokens": 2000, "topK": 10, "onlyCache": True},
        },
        "rankModelInfo": {
            "default": {
                "features": [
                    {"name": "static_value", "field": "_weather_score", "weights": 1.0},
                    {
                        "name": "qwen-rerank",
                        "fields": ["hostname", "title", "snippet", "timestamp_format"],
                        "weights": 1,
                        "threshold": -50,
                        "max_length": 5120,
                        "rank_size": 100,
                        "norm": False,
                    },
                ],
                "aggregate_algo": "weight_avg",
            }
        },
        "headers": {"__d_head_qto": 5000},
    }

    for _ in range(10):
        try:
            resp = requests.post(url, headers=headers, data=json.dumps(template))
            rst = json.loads(resp.text)
            docs = rst["data"]["docs"]
            news_list = []
            for doc in docs:
                # news_list.append('\"'+ doc['title']+ '\\n' + doc["snippet"] +'\"')
                news_list.append(doc)
            return news_list
        except Exception as e:
            print("Meet error when search query:", resp, query, e)
            print("retrying")
            time.sleep(1 * (_ + 1))
            continue
    return []

def format_results(search_results: List[Dict[str, str]]):
    formatted_results = [
        {
            'id': str(res.get('_id', '').split('.')[-1]),
            'title': str(res.get('title', '')),
            'snippet': str(res.get('snippet', '')),
            'url': str(res.get('url', '')),
            'timestamp': str(res.get('timestamp_format', ''))[:10],
            'content': str(res.get('web_main_body', '')),
        }
        for rank, res in enumerate(search_results)
    ]
    return formatted_results



def local_request(query: str, search_engine: str, freshness: str = "") -> List[Dict[str, str]]:
    """
    ElasticSearch
    """
    pass


def local_format_results(search_results: List[Dict[str, str]]):
    formatted_results = [
        {
            'id': str(res.get('doc_id', '')),
            'content': str(res.get('content', '')),
            'timestamp': str(res.get('timestamp', ''))
        }
        for rank, res in enumerate(search_results)
    ]
    return formatted_results


def _rearrange_and_dedup(doc_lists: List[List[Dict[str, str]]]) -> List[Dict[str, str]]:
    doc_list = []
    snippet_set = set()
    # print([len(i) for i in doc_lists])
    for i in range(50):
        for ds in doc_lists:
            if i < len(ds):
                if 'snippet' in ds[i]:
                    signature = ds[i]['snippet'].replace(' ', '')[:200]
                else:
                    signature = ds[i]['content'].replace(' ', '')[:200]
                if signature not in snippet_set:
                    doc_list.append(ds[i])
                    snippet_set.add(signature)
    return doc_list



if __name__ == '__main__':

    queries = ["egypt crisis timeline"]
    from pprint import pprint
    pprint(search(queries, search_engine='crisis egypt', n_max_doc=30))