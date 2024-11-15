import os
import re
from typing import List
import dashscope
import requests
import json

def rewrite_query(query: str, n_max_query: int = 5) -> List[str]:
    url = os.getenv("REWRITER_HTTP")
    headers = {
        'Authorization': 'Bearer ' + os.getenv("REWRITER_API_KEY"),
        'Content-Type': 'application/json'
    }

    data = {
        "model": os.getenv("REWRITER_MODEL_NAME"),
        "input": {
            "messages": [
                {"role": "user", "content": query}
            ]
        },
        "parameters": {
            "top_k": 1,
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "search",
                        "description": "Utilize the web search engine to retrieve relevant information based on multiple queries.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "queries": {
                                    "type": "List[str]",
                                    "description": "The list of search queries."
                                }
                            },
                            "required": ["queries"]
                        }
                    }
                }
            ],
            "tool_choice": {
                "type": "function",
                "function": {"name": "search"}
            },
            "result_format": "message"
        }
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    try:
        response = response.json()['output']['choices'][0]['message']['tool_calls'][0]['function']['arguments']
        queries = eval(response)["queries"]
    except:
        print(response.json())
        queries = [query]

    return list(set(queries[:n_max_query]))



if __name__ == '__main__':
    print(rewrite_query('深度分析AI的发展现状'))
