import os
import dashscope
from .utils import get_current_date_and_weekday
from typing import Dict, List, Tuple
from .model import query_model

def ask_news_question(model: str, news: str, docs: list = [], questions: list = []):
    input_length = 29000
    raw_prompt = _build_raw_prompt(news, docs, questions)
    try:
        responses = query_model(model, raw_prompt)
        return eval(responses)
    except Exception as e:
        try: 
            return eval(responses.replace("\'s", ""))
        except Exception as e:
            print(responses)
            return []

def _build_raw_prompt(news: str, docs: list = [], questions: list = []) -> str:
    if not docs:
        raw_prompt = "<|im_start|>system\nYou are an experienced journalist building a timeline for the target news. \n\n当前时间：{today}。\n\n你需要通过提出至少5个问题梳理新闻发展的时间线，关注事件的起源、发生原因、发展过程、来龙去脉、关键人物，侧重于事实类新闻知识而非主观评价性内容。这5个问题是独立不重合的，每个问题只包含1个子问题。所有问题总量潜在的信息量越大越好，包括的时间跨度越大越好。\n\n##输出格式：['...', '...', '...', ...]<|im_end|>\n<|im_start|>user\n{news}<|im_end|>\n<|im_start|>assistant\n"
        raw_prompt = raw_prompt.format(
            today=get_current_date_and_weekday(),
            news=news
        )
    else:
        raw_prompt = """<|im_start|>system\nYou are an experienced journalist building a timeline for the target news. \n\n当前时间：{today}。\n\n你需要基于当前相关的新闻库，通过提出至少5个【当前新闻库无法回答】的问题，继续梳理新闻发展的时间线，关注相关事件的起源、发生原因、发展过程、来龙去脉、关键人物，侧重于事实类新闻知识而非主观评价性内容。这5个问题是独立不重合的，每个问题只包含1个子问题。所有问题总量潜在的信息量越大越好，包括的时间跨度越大越好，不要提和已搜索问题集中类似的问题。直接按照规定的格式输出你的问题。\n\n##输出格式：['...', '...', '...', ...]<|im_end|>\n<|im_start|>user\nTarget news:{news}\n\n当前相关的新闻库:{docs}\n\n已搜索问题集:{questions}<|im_end|>\n<|im_start|>assistant\n"""
        raw_prompt = raw_prompt.format(
            today=get_current_date_and_weekday(),
            news=news,
            docs=''.join([f'\n"资料 {i}:\n  标题: {doc["title"]}\n  时间: {doc["timestamp"]}\n  摘要: {doc["snippet"]}"\n' for i, doc in enumerate(docs, 1)]),
            questions=questions
        )
    print(raw_prompt)
    return raw_prompt
