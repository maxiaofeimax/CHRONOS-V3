# CHRONOS-V3

CHRONOS-V3 是一个基于 Streamlit 的新闻时间线生成工具，支持多轮新闻事件梳理、智能问题生成、新闻摘要与时间线自动合成。

## 主要功能
- 输入新闻事件，自动搜索相关资料
- 智能生成多轮提问，梳理新闻发展脉络
- 自动生成新闻时间线与摘要
- 支持全文阅读与多种搜索引擎

## 快速开始
1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
2. 配置环境变量（可选，见 `.env` 文件说明）
3. 运行应用：
   ```bash
   streamlit run app.py
   ```

## 目录结构
- `app.py`：主应用入口
- `requirements.txt`：依赖列表
- `src/`：核心功能模块

## 环境变量说明
- `MODEL_NAME`、`OPENAI_API_KEY`、`DASHSCOPE_API_KEY`、`SEARCH_API_KEY` 等需根据实际情况配置

## 贡献
欢迎提交 issue 和 PR！

---
Auto-uploaded by MCP tool.