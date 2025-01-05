import dashscope
import requests
import json
import os

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

def query_model(model: str, raw_prompt: str):
    responses = None
    try_time = 0
    while (responses == None and try_time < 15):
        if 'qwen' in model:
            responses = query_qwen(model, raw_prompt)
        elif 'gpt' in model:
            responses = query_gpt(model, raw_prompt)
        try_time += 1
    return responses

def query_qwen(model: str, raw_prompt: str):
    try:
        dashscope.base_http_api_url=os.getenv('DASHSCOPE_BASE_HTTP')
        dashscope.base_websocket_api_url=os.getenv('DASHSCOPE_BASE_WEBSOCKET')
        resp = dashscope.Generation.call(
            api_key=os.getenv('DASHSCOPE_API_KEY'),
            model=model,
            prompt=raw_prompt,
            use_raw_prompt=True
        )
        responses = resp['output']['text']
        return responses
    except:
        print(resp)

def query_gpt(model: str, raw_prompt: str):
    headers = {
                "Content-Type": "application/json",
                "Authorization": f'Bearer {OPENAI_API_KEY}'
            }
    r = requests.post(os.getenv('OPENAI_BASE_HTTP'), 
        data=json.dumps({
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": raw_prompt
                    }
                ]
            }),
        headers=headers)
    resp = json.loads(r.text)
    answer = resp['data']['response']
    responses = answer['choices'][0]['message']['content']
    return responses