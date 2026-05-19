import asyncio
import time
from collections.abc import Sequence

import httpx
from loguru import logger

from async_crawler.models import FetchStatus, PageResult
from async_crawler.parser import parse_html


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
    except httpx.TimeoutException as e:  # 超时错误，
        logger.warning(f"超时:{url} 耗时:{time.perf_counter()-start:.2f}s")
        return PageResult(
            url=url,
            status=FetchStatus.TIMEOUT,
            elapsed_ms=time.perf_counter() - start,
            error=f"timeout {str(e)}",
        )
    except httpx.ConnectError as e:  # 网络连接错误
        logger.warning(f"连接错误:{url} 耗时:{time.perf_counter()-start:.2f}s 报错:{e}")
        return PageResult(
            url=url,
            status=FetchStatus.NETWORK_ERROR,
            elapsed_ms=time.perf_counter() - start,
            error=f"connect_error {str(e)}",
        )
    except httpx.HTTPError as e:  # 其他未知错误
        logger.warning(f"http错误:{url} 耗时:{time.perf_counter()-start:.2f}s 报错:{e}")
        return PageResult(
            url=url,
            status=FetchStatus.HTTP_ERROR,
            elapsed_ms=time.perf_counter() - start,
            error=f"http_error {type(e).__name__}",
        )

    # 非200错误
    if response.status_code != 200:  # 4xx 5xx
        logger.warning(
            f"code错误，f{url}, code:{response.status_code}, 耗时:{time.perf_counter()-start:.2f}"
        )
        return PageResult(
            url=url,
            status=FetchStatus.HTTP_ERROR,
            http_code=response.status_code,
            elapsed_ms=time.perf_counter() - start,
            error=f"code_error {response.status_code}",
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
            elapsed_ms=time.perf_counter() - start,
            error=f"parse_error:{str(e)}",
        )

    logger.success(f"解析OK，url:{url} 耗时:{time.perf_counter()-start:.2f}")
    return PageResult(
        url=url,
        status=FetchStatus.OK,
        http_code=response.status_code,
        elapsed_ms=time.perf_counter() - start,
        content=content,
    )


# 请求多个url的内容


async def fetch_many(
    urls: Sequence[str], concrurrency: int = 5, timeout: float = 15
) -> list[PageResult]:
    """
    批量并发抓取 URL。
    用 Semaphore 限流,用 TaskGroup 管理生命周期。
    """
    # 连接池配置
    timeout = httpx.Timeout(connect=5, read=timeout, write=30, pool=60)
    limit = httpx.Limits(max_connections=concrurrency * 2, max_keepalive_connections=concrurrency)
    headers = {
        "Accept": "text/html,application/xhtml+xml",
    }
    # 信号量管理并发数量
    semaphore = asyncio.Semaphore(concrurrency)

    # async with 异步上下文 管理信号量并发数
    async def _bounded_fetch(client: httpx.AsyncClient, url: str) -> PageResult:
        """所有任务通过信号量 控制并发数"""
        async with semaphore:
            return await fetch_one(client=client, url=url)

    # async with 异步上下文 管理请求连接池
    async with httpx.AsyncClient(timeout=timeout, limits=limit, headers=headers) as client:
        # async with 异步上下文 管理 TaskGroup并发协程
        async with asyncio.TaskGroup() as tg:
            # 生成 协程任务 task
            tasks = [tg.create_task(_bounded_fetch(client=client, url=url)) for url in urls]

    # 退出 TaskGroup 后,所有任务都完成了
    return [task.result() for task in tasks]
