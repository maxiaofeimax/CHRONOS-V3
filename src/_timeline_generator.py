import os
import dashscope
from .utils import get_current_date_and_weekday
from typing import Dict, List, Tuple
import json
from .model import query_model

def generate_timeline(model: str, news: str, docs: list):
    input_length = 30000
    raw_prompt = _build_raw_prompt(news, docs)
    try:
        responses = query_model(model, raw_prompt)
        return post_process(responses)
    except Exception as e:
        raise ValueError(f'Call dashscope failed.\nPlease try again later or decrease the amount of referenced news articles.') 

def merge_timeline(model: str, news: str, summaries: list, timelines: list):
    input_length = 30000
    raw_prompt = _build_raw_prompt_merge(news, summaries, timelines)
    try:
        responses = query_model(model, raw_prompt)
        return post_process(responses)
    except Exception as e:
        raise ValueError(f'Call dashscope failed.\nPlease try again later or decrease the amount of referenced news articles.') 


def _build_raw_prompt(news: str, docs: list) -> str:
    raw_prompt = """<|im_start|>system\nYou are an experienced journalist writing a background story and building a timeline for the target news. \n\n当前时间：{today}。\n\n当前相关的新闻库:{docs}\n\n
        指令：
        第1步：阅读每条背景新闻，并从您的新闻库中提取所有与目标新闻相关的事件，同时对应其日期。为每个事件起一个不超过6个字的简短标题，事件描述应包含该事件的关键细节信息，并将所有事件保存为列表。格式为：[{{"content": <简短标题>, "start": <日期|格式如2023-02-02>, "summary": <事件描述>}}, ...]
        第2步：严格按照时间顺序，使用第1步中提取的事件，撰写一篇关于目标新闻的详细的、连贯的背景故事，严格按照从早到晚的时间顺序，全面地阐述新闻的来龙去脉，包含每一件事件的所有细节。使用'\n'来连接不同日期的新闻。其中所有涉及到的日期使用格式如2023-02-02的表示。
        第3步：根据您所写的背景故事，重新组织您的事件列表以形成最终的时间线，遵循以下指示：(1) 删除那些未在背景故事中提及的事件，(2) 按日期对列表进行排序。timeline中的事件描述"summary"不需要再标注日期，只需要呈现新闻事件具体细节。
        
        按照以下格式直接输出你的答案，格式为一个json对象：
        {{ 
            "events": [{{"id": <序号|格式如1>, "content": <简短标题>, "start": <日期|格式如2023-02-02>, "summary": <事件描述>}}, ...], 
            "background_summary": "一段详细连贯的摘要，按照时间线为目标新闻提供更深入的见解" ,
            "final_timeline": [{{"id": <序号|格式如1>, "content": <简短标题>, "start": <日期|格式如2023-02-02>, "summary": <事件描述>}}, ...]
        }}
        
        <|im_end|>\n<|im_start|>user\nTarget News: {news}<|im_end|>\n<|im_start|>assistant\n"""
    
    raw_prompt = raw_prompt.format(
        today=get_current_date_and_weekday(),
        news=news,
        docs=''.join([f'\n"资料 {i}:\n  标题: {doc["title"]}\n  时间: {doc["timestamp"]}\n  摘要: {doc["snippet"]}"\n' for i, doc in enumerate(docs, 1)])
    )

    print(raw_prompt)
    return raw_prompt

def _build_raw_prompt_merge(news: str, summaries: list, timelines) -> str:

    raw_prompt = """<|im_start|>system\nYou are an experienced journalist writing a background story and building a timeline for the target news. \n\n按照时间顺序，合并已有的新闻摘要和时间线。
    ##新闻摘要: {summaries}
    ##时间线: {timelines}
    合并新闻摘要时删除非新闻事件的部分，严格按照时间从前往后的顺序，用\\n隔开不同日期发生的事件。合并时间线时，删除非新闻事件的item, id按照事件发生先后顺序，从1开始依次增加，不要重复。按照以下格式直接输出你的答案，格式为一个json对象：
    {{ 
        "background_summary": "一段详细连贯的摘要，按照时间线为目标新闻提供更深入的见解。每当开始写一个新日期时发生的事件，用\\n隔开。" ,
        "final_timeline": [{{"id": <序号|格式如1>, "content": <简短标题>, "start": <日期|格式如2023-02-02>, "summary": <事件描述>}}, ...]
    }}
    
    <|im_end|>\n<|im_start|>user\nTarget News: {news}<|im_end|>\n<|im_start|>assistant\n"""
    raw_prompt = raw_prompt.format(
        today=get_current_date_and_weekday(),
        news=news,
        summaries=summaries,
        timelines=timelines
    )
    
    print(raw_prompt)
    return raw_prompt


def post_process(output):
    try:
        output = json.loads(output)
    except:
        import re
        pattern = r"```json(.*?)```"
        matches = re.findall(pattern, output, re.DOTALL)
        output = matches[-1].strip()
        output = json.loads(output.lstrip("```json").strip("```"))
    return output['background_summary'], output['final_timeline']
