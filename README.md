# async-crawler

> 基于 Python asyncio + httpx 的异步并发爬虫 CLI 工具。
> 演示项目,展示现代 Python 工程实践:类型注解、Pydantic、asyncio、Typer、pytest。

[![CI](https://github.com/holisfei/async-crawler/actions/workflows/ci.yml/badge.svg)](https://github.com/holisfei/async-crawler/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-passing-green.svg)]()
[![Coverage](https://img.shields.io/badge/coverage-85%25-green.svg)]()

## 特性

- ⚡ **异步并发**:基于 asyncio.TaskGroup 和 asyncio.as_completed,默认并发数5,可调
- 🛡️ **错误分类**:超时 / HTTP / 网络 / 解析错误分别归类,失败不抛异常而作为数据返回
- 📊 **丰富输出**:rich 进度条 + 统计表格 + 失败 URL 详情
- 📦 **结构化结果**:Pydantic 模型 + JSON 输出,可直接喂给下游
- 🧪 **测试齐全**:pytest + pytest-asyncio + pytest-httpx, 覆盖率 > 90%

## 快速开始

### 安装

需要 Python 3.12+。

```bash
git clone https://github.com/holisfei/async-crawler.git
cd async_crawler
uv sync
```

### 用法

```bash
# 抓取几个 URL
uv run mycrawler fetch https://example.com https://example.org

# 从文件读 URL 列表
uv run mycrawler fetch --from-file urls.txt -c 10

# 自定义输出文件和超时
uv run mycrawler fetch --from-file urls.txt -o data.json -t 30

# 安静模式(适合脚本调用)
uv run mycrawler fetch --from-file urls.txt --quiet
```

### 示例输出

![image](https://github.com/holisfei/async-crawler/raw/main/resource/result.png)

## 项目结构
```
src/async_crawler/
├── models.py     # Pydantic 数据模型 (PageContent, PageResult, FetchStatus)
├── parser.py     # HTML 解析 (selectolax)
├── fetcher.py    # 异步抓取核心 (httpx + asyncio)
└── cli.py        # Typer CLI 入口
tests/
├── conftest.py
├── test_parser.py
├── test_fetcher.py
└── test_cli.py
```

## 开发

```bash
# 测试
uv run pytest

# 覆盖率
uv run pytest --cov=async_crawler --cov-report=html

# 代码检查
uv run ruff check . && uv run ruff format .
uv run mypy src/
```
## 技术栈

| 用途 | 选型 | 备注 |
|---|---|---|
| 包管理 | uv | Rust 实现,比 pip 快 10-100 倍 |
| HTTP 客户端 | httpx | 原生异步,连接池友好 |
| HTML 解析 | selectolax | C 实现,比 lxml 快 2-3 倍 |
| 数据校验 | Pydantic v2 | LLM 应用事实标准 |
| CLI | Typer | 基于类型注解,自动生成 --help |
| 终端 UI | rich | 进度条 / 表格 / 彩色输出 |
| 日志 | loguru | 异步友好 |
| 测试 | pytest + asyncio + httpx | mock 异步请求 |
| 代码质量 | ruff + mypy | Rust 实现的 lint/format |
