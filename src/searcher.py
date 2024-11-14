import os
import json
import requests
import concurrent.futures
import logging
from typing import Dict, List


def search(query_list: List[str], n_max_doc: int = 20, search_engine: str = 'bing', freshness: str = '') -> List[Dict[str, str]]:
    doc_lists = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(search_single, query, search_engine, freshness) for query in query_list]
        for future in concurrent.futures.as_completed(futures):
            try:
                doc_lists.append(future.result())
            except:
                pass
    doc_list = _rearrange_and_dedup([d for d in doc_lists if d])
    return doc_list[:n_max_doc]


def search_single(query: str, search_engine: str, freshness: str = '') -> List[Dict[str, str]]:
    try:
        if search_engine == 'bing':
            search_results = bing_request(query, freshness=freshness)
            return bing_format_results(search_results)
        else:
            search_results = local_request(query, search_engine)
            return local_format_results(search_results)
    except Exception as e:
        logging.error(f'Search failed: {str(e)}')
        raise ValueError(f'Search failed: {str(e)}')


def bing_request(query: str, count: int = 50, freshness: str = '') -> List[Dict[str, str]]:
    headers = {
            'Authorization': 'Bearer ' + os.getenv("BING_API_KEY"),
            'Content-Type': 'application/json'
        }

    if freshness:
        payload = {
            "rid": "",
            "scene": os.getenv("BING_SCENE"),
            "uq": query,		
            "debug": True,
            "fields": [],
            "page": 1,
            "rows": count,
            "customConfigInfo": {},
            "freshness": f"1970-01-01..{freshness}",
        }
    else:
        payload = {
            "rid": "",
            "scene": os.getenv("BING_SCENE"),
            "uq": query,		
            "debug": True,
            "fields": [],
            "page": 1,
            "rows": count,
            "customConfigInfo": {}
        }
    
    response = requests.post(os.getenv("BING_HTTP"), json=payload, headers=headers)

    search_results = response.json()['data']['docs']
    return search_results


def bing_format_results(search_results: List[Dict[str, str]]):
    formatted_results = [
        {
            'id': str(res.get('_id', '').split('.')[-1]),
            'title': str(res.get('title', '')),
            'snippet': str(res.get('snippet', '')),
            'url': str(res.get('url', '')),
            'timestamp': str(res.get('timestamp_format', ''))[:10]
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