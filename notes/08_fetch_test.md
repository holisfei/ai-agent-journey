# 爬虫请求逻辑

整个架构设计
```python
┌─────────────────────────────────────────────┐
│  fetch_many(urls, concurrency)              │  ← 批量入口
│    └→ 用 Semaphore + TaskGroup 并发        │
└─────────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│  fetch_one(client, url)                     │  ← 单 URL 抓取
│    └→ httpx 请求 + 错误分类 + 调用 parser  │
└─────────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│  httpx.AsyncClient                          │  ← 底层连接池
└─────────────────────────────────────────────┘
```

示例：
```py
import asyncio
import httpx
import time
from async_crawler.models import FetchStatus, PageResult
from async_crawler.parser import parse_html
from loguru import logger
from typing import Sequence

# 请求单个url的内容
async def fetch_one(client: httpx.AsyncClient, url: str) -> PageResult:
    """
    抓单个 URL,并解析 HTML 为结构化内容。
    任何异常都被捕获,转换为带状态的 PageResult。
    """

    # ⚠️ 这里逻辑 不抛出异常，而是使用model表示异常
    # 因为作为taskGroup的字协程任务，任何一个任务抛出异常，其余任务会取消所以这里
    # 所以：这里使用了model去return一个错误的结果，相当于吃掉了raise抛异常这个逻辑

    start = time.perf_counter()
    try:
        response = await client.get(url=url, follow_redirects=True)
    except httpx.TimeoutException as e: # 超时错误，
        logger.warning(f"超时:{url} 耗时:{time.perf_counter()-start:.2f}s")
        return PageResult(
            url=url,
            status=FetchStatus.TIMEOUT,
            elapsed_ms=time.perf_counter()-start,
            error=f"timeout {str(e)}"
        )
    except httpx.ConnectError as e: # 网络连接错误
        logger.warning(f"连接错误:{url} 耗时:{time.perf_counter()-start:.2f}s 报错:{e}")
        return PageResult(
            url=url,
            status=FetchStatus.NETWORK_ERROR,
            elapsed_ms=time.perf_counter()-start,
            error=f"connect_error {str(e)}"
        )
    except httpx.HTTPError as e: # 其他未知错误
        logger.warning(f"http错误:{url} 耗时:{time.perf_counter()-start:.2f}s 报错:{e}")
        return PageResult(
            url=url,
            status=FetchStatus.HTTP_ERROR,
            elapsed_ms=time.perf_counter()-start,
            error=f"http_error {type(e).__name__}"
        )

    # 非200错误
    if response.status_code != 200: # 4xx 5xx
        logger.warning(f"code错误，f{url}, code:{response.status_code}, 耗时:{time.perf_counter()-start:.2f}")
        return PageResult(
            url=url,
            status=FetchStatus.HTTP_ERROR,
            http_code=response.status_code,
            elapsed_ms=time.perf_counter()-start,
            error=f"code_error {response.status_code}"
        )

    # 解析内容
    try:
        content = parse_html(html=response.text)
    except Exception as e:
        logger.error(f"解析错误:{url}, code:{response.status_code}, err:{str(e)}")
        return PageResult(
            url=url,
            status=FetchStatus.PARSE_ERROR,
            http_code=response.status_code,
            elapsed_ms=time.perf_counter()-start,
            error=f"parse_error:{str(e)}"
        )

    logger.success(f"解析OK，url:{url} 耗时:{time.perf_counter()-start:.2f}")
    return PageResult(
        url=url,
        status=FetchStatus.OK,
        http_code=response.status_code,
        elapsed_ms=time.perf_counter()-start,
        content=content
    )


# 请求多个url的内容

async def fetch_many(urls:Sequence[str], concrurrency:int=5, timeout:float=15) -> list[PageResult]:
    """
    批量并发抓取 URL。
    用 Semaphore 限流,用 TaskGroup 管理生命周期。
    """
    # 连接池配置
    timeout = httpx.Timeout(connect=5, read=timeout, write=30, pool=60)
    limit = httpx.Limits(max_connections=concrurrency*2, max_keepalive_connections=concrurrency)
    headers = {
        "Accept": "text/html,application/xhtml+xml",
    }
    # 信号量管理并发数量
    semaphore = asyncio.Semaphore(concrurrency)

    # async with 异步上下文 管理信号量并发数
    async def _bounded_fetch(client:httpx.AsyncClient, url:str) -> PageResult:
        """所有任务通过信号量 控制并发数"""
        async with semaphore:
            return await fetch_one(client=client, url=url)

    # async with 异步上下文 管理请求连接池
    async with httpx.AsyncClient(timeout=timeout, limits=limit, headers=headers) as client:
        # async with 异步上下文 管理 TaskGroup并发协程
        async with asyncio.TaskGroup() as tg:
            # 生成 协程任务 task
            tasks = [tg.create_task(_bounded_fetch(client=client,url=url)) for url in urls]

    # 退出 TaskGroup 后,所有任务都完成了
    return [task.result() for task in tasks]
```

### 核心逻辑
#### 1. 错误分类与捕获顺序

```py
try:
    response = await client.get(url, ...)
except httpx.TimeoutException as e:     # 必须先捕获子类
    ...
except httpx.HTTPError as e:             # 再捕获父类
    ...
```
httpx.TimeoutException 是 httpx.HTTPError 的子类。Python 异常匹配是从上到下找第一个匹配的,子类必须写在父类之前,否则永远走不到子类分支。

#### 2. 「任何异常都不让 fetch_one 抛出」

注意整个 fetch_one 函数,捕获了所有可能的异常,返回的永远是 PageResult——失败也是一种结果,不是异常。

如果某个协程任务抛出异常，Taskgroup管理的其余并发协程任务都会被取消，外部拿不到任何结果。

所以，让失败变成数据,而不是异常——这是函数式风格的错误处理,调用方代码极简洁。

#### 3. Semaphore 并发数量管理

使用 Semaphore 管理所有协程任务的并发数，包在 fetch_one 外面,不要包在 fetch_one 里面。原因:fetch_one 是「业务逻辑函数」,limit 是「调度策略」,分层别混。

#### 4. TaskGroup 比 gather 强在哪

任一任务异常 → 自动取消其他任务、释放资源(这里我们捕获了所有异常作为model返回值,不会触发)

通过 async with 异步上下文 保证退出时所有任务都被妥善处理

配合 tg.create_task 比 gather 的语义更清晰

#### 5. 全局 client 还是按需 client

AsyncClient 持有连接池资源,必须在事件循环里创建并显式关闭。放模块顶层会:

- 创建时没有事件循环可能出问题
- 不能保证关闭,有资源泄漏风险

async with 会自动管生连接池的生命周期

#### 6. 为什么用 Sequence 不用 list 做参数类型

「参数收宽松,返回收具体」原则。

函数只是遍历 urls,不会修改它,所以接收 Sequence(可以是 list、tuple、generator),调用方更灵活。返回类型用具体的 list[PageResult],调用方能放心索引。

# 测试:pytest-httpx mock 网络请求

爬虫测试不能依赖真实网络(慢、不稳、对方可能挂)。用 pytest-httpx mock httpx 的请求。

添加依赖：```uv add --dev pytest-httpx pytest-asyncio```
- pytest-asyncio: 让 pytest 能跑 async def 测试函数
- pytest-httpx: 拦截 httpx 请求,返回你预设的假响应

在 pyproject.toml 加:
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"           # 所有 async def 测试自动用 asyncio 跑
```

### pytest-httpx 的匹配规则

规则:所有参数都是「匹配条件」,不写就匹配任何值
add_response() 的所有参数都是两类:
- 匹配条件(决定哪些请求被这个 mock 拦下来)，不写 = 匹配任何
    - url、method、match_headers、match_json
- 响应内容(被拦下后返回什么)，必须的(否则返回 200 + 空 body)
    - status_code、text、json、html

### 几个高级匹配条件

```py
# 按 HTTP 方法
httpx_mock.add_response(method="POST", ...)

# 按请求头
httpx_mock.add_response(match_headers={"Authorization": "Bearer xxx"}, ...)

# 按请求体 JSON
httpx_mock.add_response(match_json={"key": "value"}, ...)

# 按 URL 正则(不常用)
import re
httpx_mock.add_response(url=re.compile(r"https://api\.example\.com/v\d+/users"), ...)
```

示例：
```py
import pytest
import httpx
from pytest_httpx import HTTPXMock
from async_crawler.fetcher import fetch_one, fetch_many
from async_crawler.models import FetchStatus

class TestFetchOne:
    async def test_one_success(self, httpx_mock: HTTPXMock):
        html = "<html><head><title>Test</title></head><body><h1>Hi</h1></body></html>"
        url = "https://example.com"
        httpx_mock.add_response(
            url=url,
            status_code=200,
            text=html
        )

        async with httpx.AsyncClient() as client:
            result = await fetch_one(client=client, url=url)

        assert result.status == FetchStatus.OK
        assert result.http_code == 200
        assert result.error is None
        assert result.content is not None
        assert result.content.title == "Test"
        assert "Hi" in result.content.headings
        assert result.elapsed_ms > 0

    async def test_one_404(self, httpx_mock: HTTPXMock):
        url = "https://example.com/missing"
        httpx_mock.add_response(
            url=url,
            status_code=404,
            text="Not Found",
        )

        async with httpx.AsyncClient() as client:
            result = await fetch_one(url=url, client=client)

        assert result.status == FetchStatus.HTTP_ERROR
        assert result.http_code == 404
        assert result.content is None

    async def test_one_500(self, httpx_mock: HTTPXMock):
        """5xx 响应也归类为 HTTP_ERROR"""

        url = "https://example.com/oops"
        httpx_mock.add_response(
            url=url,
            status_code=500
        )

        async with httpx.AsyncClient() as client:
            result = await fetch_one(client=client, url=url)

        assert result.status == FetchStatus.HTTP_ERROR
        assert result.http_code == 500

    async def test_one_timeout(self, httpx_mock: HTTPXMock):
        """超时应该被分类为 TIMEOUT"""
        url = "https://example.com"
        httpx_mock.add_exception(
            exception=httpx.TimeoutException("timed out"),
            url=url
        )

        async with httpx.AsyncClient() as client:
            result = await fetch_one(client=client, url=url)

        assert result.status == FetchStatus.TIMEOUT
        assert result.content is None
        assert "timed out" in result.error.lower()

    async def test_one_connection_error(self, httpx_mock: HTTPXMock):
        """连接错误应该被分类为 NETWORK_ERROR"""
        url = "https://example.com"
        httpx_mock.add_exception(
            exception=httpx.ConnectError("connection refused"),
            url=url
        )

        async with httpx.AsyncClient() as client:
            result = await fetch_one(client=client, url=url)

        assert result.status == FetchStatus.NETWORK_ERROR
        assert result.content is None

class TestFetchMany:
    async def test_many_all_success(self, httpx_mock: HTTPXMock):
        """并发 都成功"""

        base_url = "https://example.com"
        urls = [f"{base_url}/{i}" for i in range(5)]
        for i, url in enumerate(urls):
            httpx_mock.add_response(
                url=url,
                status_code=200,
                text=f"<html><head><title>Page {i}</title></head><body></body></html>"
            )

        results = await fetch_many(urls=urls, concrurrency=3)

        assert len(results) == 5
        for i, res in enumerate(results): # 验证返回结果的顺序
            assert res.url == f"{base_url}/{i}"
            assert res.status == FetchStatus.OK
            assert res.content.title == f"Page {i}"

    async def test_many_part_success(self, httpx_mock: HTTPXMock):
        """并发 部分成功"""

        url1 = "https://example.com/ok"
        url2 = "https://example.com/notfound"
        url3 = "https://example.com/slow"
        text = "<html><head><title>OK</title></head><body></body></html>"
        httpx_mock.add_response(url=url1, status_code=200, text=text)
        httpx_mock.add_response(url=url2, status_code=404, text="not found")
        httpx_mock.add_exception(exception=httpx.TimeoutException("time out"), url=url3)

        results = await fetch_many(urls=[url1, url2, url3], concrurrency=3)

        assert len(results) == 3
        assert results[0].status == FetchStatus.OK
        assert results[0].content.title == "OK"
        assert results[1].status == FetchStatus.HTTP_ERROR
        assert results[2].status == FetchStatus.TIMEOUT

    async def test_empty_url_list(self):
        """空列表应该返回空列表"""
        results = await fetch_many([])
        assert results == []
```

#  Anki 卡片

```py
Q: 把失败转成数据 vs 抛出异常,哪个更好?
A: 数据。调用方代码更清爽,容易聚合统计

Q: httpx 异常捕获要注意什么?
A: 子类(TimeoutException)写在父类(HTTPError)之前

Q: Python 3.11+ 推荐的并发原语?
A: asyncio.TaskGroup,比 gather 更安全

Q: 测试 httpx 异步代码用什么?
A: pytest-asyncio + pytest-httpx

Q: pytest-httpx mock 异常?
A: httpx_mock.add_exception(httpx.TimeoutException(...))

Q: AsyncClient 应该在哪里创建?
A: async with 在使用处,不要放模块顶层

Q: Semaphore 应该包在业务函数里还是外面?
A: 外面。业务函数管业务,限流是调度,分层别混
```
