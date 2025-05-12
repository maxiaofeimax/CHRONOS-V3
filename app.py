import streamlit as st
from streamlit_timeline import st_timeline

st.set_page_config(page_title="统计语言模型发展的里程碑", layout="wide")

# items = [
#     {"id": 1, "content": "N-Gram模型", "start": "1948"},
#     {"id": 2, "content": "Bag-of-Words模型", "start": "1954"},
#     {"id": 3, "content": "分布式表示法", "start": "1986"},
#     {"id": 4, "content": "神经概率语言模型", "start": "2003"},
#     {"id": 5, "content": "Word2Vec", "start": "2013"},
#     {"id": 6, "content": "预训练语言模型", "start": "2018"}
# ]


timeline = st_timeline(items, groups=[], options={}, height="300px")
st.subheader("选中的事件")
st.write(timeline)
