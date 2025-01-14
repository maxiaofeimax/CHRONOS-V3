import time
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from http import HTTPStatus
from src.rewriter import rewrite_query
from src.searcher import search
from src.reader import read_pages
from src._questioner import ask_news_question
# from src._news_retriever import news_filter
from src._timeline_generator import generate_timeline, merge_timeline
import jsonlines
from streamlit_timeline import st_timeline
import os
from concurrent.futures import ThreadPoolExecutor, as_completed



load_dotenv()
st.set_page_config(layout="wide")
st.title('🗓️ CHRONOS新闻时间线生成')

chat_model = os.getenv('MODEL_NAME')

examples = [
    '国足1-0巴林队',
    '小米15发布',
    '中国探月工程'
]

with st.sidebar:
    MAX_ROUNDS = st.number_input('提问轮数：', min_value=0, max_value=10, value=2, step=1)
    # n_max_query = st.number_input('问题拆解上限：', min_value=1, max_value=6, value=3, step=1)
    n_max_doc = st.number_input('引用资料上限：', min_value=1, max_value=50, value=10, step=5)
    read_page = st.checkbox('阅读新闻资料全文', False)
    selected_example = st.sidebar.selectbox('示例：', examples)


def news_timeline_generation(input_text):
    """
    {
        "event": title,
        "start": timestamp,
        "summary": summary
    }
    """
    news_timeline = []
    search_engine = 'google'
    n_max_query = 3
    doc_list_all = search([input_text], 10, search_engine)    # 先直接按keywords进行搜索
    with st.popover(f'直接搜索目标新闻，引用 {len(doc_list_all)} 篇资料作为参考'):
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown('\n\n'.join([f'{d["title"]}' for d in doc_list_all]))
        with col2:
            st.markdown('\n\n'.join([f'{d["url"]}' for d in doc_list_all]))
    question_list_all = []
    summaries = []
    timelines = []

    main_cols = st.columns(MAX_ROUNDS)
    for i in range(1, MAX_ROUNDS + 1):
        question_time, rewrite_time, search_time, generate_time, read_time = 0,0, 0, 0, 0
        tic0 = tic = time.time()
        with main_cols[i-1]:
            st.markdown(f'**第{i}次提问...**')
        question_list = ask_news_question(model=chat_model, news=input_text, docs=doc_list_all, questions=question_list_all)  # question-based news background decomposition
        question_time += time.time() - tic
        # st.success('\n'.join(f'- {q}' for q in question_list))


        tic = time.time()
        query_list = {}
        queries = []
        # for question in question_list:
        #     print(question)
        #     query_gen = rewrite_query(question, n_max_query) # 改写
        #     # query_gen = [question]
        #     print(query_gen)
        #     query_list[question] = list(set(query_gen))
        #     queries += query_gen
        # question_list_all += queries
        def process_question(question):
            query_gen = rewrite_query(question, n_max_query)  # 改写
            query_list[question] = list(set(query_gen))
            return query_gen

        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_question = {executor.submit(process_question, question): question for question in question_list}
            for future in as_completed(future_to_question):
                question = future_to_question[future]
                try:
                    query_gen = future.result()
                except Exception as exc:
                    print('%r generated an exception: %s' % (question, exc))
                else:
                    queries.extend(query_gen)
        question_list_all += queries
        rewrite_time += time.time() - tic
        
        
        # st.markdown('**联网搜索：**')
        # st.success('\n'.join([f'- {q}' for q in query_list]))
        query_show = ""
        for question in query_list:
            query_show += f'- {question}\n'
            for q in query_list[question]:
                query_show += f'    + {q}\n'
        with main_cols[i-1]:
            with st.expander("点击展开/折叠提问", expanded=True):
                st.success(query_show.strip('\n'))

        tic = time.time()
        doc_list = search(list(set(queries)), n_max_doc, search_engine, read_page) # 搜索
        search_time += time.time() - tic

        with main_cols[i-1]:
            with st.popover(f'引用 {len(doc_list)} 篇资料作为参考'):
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.markdown('\n\n'.join([f'{d["title"]}' for d in doc_list]))
                with col2:
                    st.markdown('\n\n'.join([f'{d["url"]}' for d in doc_list]))

        
        if read_page and search_engine != 'google':
            tic = time.time()
            with main_cols[i-1]:
                with st.spinner('正在阅读网页...'):
                    if search_engine == 'bing':
                        doc_list = read_pages(doc_list, "jina")   # read page
            
            if len(doc_list) == 0:
                with main_cols[i-1]:
                    st.error('readpage结果为空!')
                # return
                retry = 0
                while len(doc_list) == 0 and retry < 5:
                    if search_engine == 'bing':
                        time.sleep(3)
                        doc_list = read_pages(doc_list, "jina")   # read page
                    retry += 1
                if retry == 5:
                    with main_cols[i-1]:
                        st.warning("READ PAGE FAILURE!!!")
            read_time += time.time() - tic

        doc_list_filtered = []
        if i == 1:
            for d in doc_list_all:
                doc_list_filtered.append(d)
        for d in doc_list:
            if d not in doc_list_all:
                doc_list_all.append(d)
            if d not in doc_list_filtered:
                doc_list_filtered.append(d)
        with main_cols[i-1]:
            st.success(str(len(doc_list_all)) + '篇网页已搜索')
        
        tic = time.time()
        with main_cols[i-1]:
            st.markdown(f'**第{i}轮时间线生成中...**')
        summary, news_timeline = generate_timeline(model=chat_model, news=input_text, docs=doc_list_filtered)    # generate timeline
        summaries.append(summary)
        timelines.append(news_timeline)
        generate_time += time.time() - tic
        
        debug_info = f'- 第{i}轮问题生成耗时：{question_time:.3f} s'
        debug_info += f'\n- 问题改写耗时：{rewrite_time:.3f} s'
        debug_info += f'\n- 新闻搜索耗时：{search_time:.3f} s'
        debug_info += f'\n- 时间线生成耗时：{generate_time:.3f} s'
        if read_page and search_engine != 'google':
            debug_info += f'\n- 新闻全文阅读耗时：{read_time:.3f} s'
        with main_cols[i-1]:
            st.warning(debug_info)

    tic = time.time()
    if MAX_ROUNDS > 1:
        st.markdown(f'**合并时间线中...**')
        summary, news_timeline = merge_timeline(model=chat_model, news=input_text, summaries=summaries, timelines=timelines)
    # else:
    #     st.markdown(f'**整理时间线中...**')
    #     summary, news_timeline = generate_timeline(model=chat_model, news=input_text, docs=doc_list_filtered)
    generate_time += time.time() - tic

    return summary, news_timeline
    

with st.form('my_form'):
    text = st.text_input('', value=selected_example, placeholder='请输入你想查询的新闻')
    submit_button = st.form_submit_button('搜索')

    if submit_button:
        if text:
            st.session_state.summary, st.session_state.news_timeline = news_timeline_generation(text)
        else:
            st.error('请输入新闻')

if 'summary' in st.session_state and st.session_state.summary:
    st.markdown('**新闻时间线总结**')
    if '\n' not in st.session_state.summary:
        process_q = []
        for q in st.session_state.summary.split('。'):
            if q!= '':
                if q[0].isdigit() or process_q == []:
                    process_q.append(q.strip('。')+'。')
                else:
                    process_q[-1] += q.strip('。')+'。'
        st.markdown('\n\n'.join(process_q))
    else:
        if '\\n' in st.session_state.summary:
            st.markdown(st.session_state.summary.replace('\\n', '\\n\\n'))
        else:
            st.markdown(st.session_state.summary.replace('\n', '\n\n'))
    
if 'news_timeline' in st.session_state and st.session_state.news_timeline:    
    processed_tl = []
    for item in st.session_state.news_timeline:
        if 'start' in item:
            if len(item['start']) > 4:
                processed_tl.append(item)
    st.session_state.news_timeline = processed_tl
    st.session_state.timeline = st_timeline(st.session_state.news_timeline, groups=[], options={"selectable": True, "multiselect": True, "verticalScroll": True}, height='300px')
    st.markdown("**Selected News**")
    st.write(st.session_state.timeline)
