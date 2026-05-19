from unittest.mock import patch

import httpx
import pytest
from pytest_httpx import HTTPXMock

from async_crawler.fetcher import fetch_many, fetch_one
from async_crawler.models import FetchStatus


class TestFetchOne:
    async def test_one_success(self, httpx_mock: HTTPXMock):
        """单个 抓取 成功"""
        html = "<html><head><title>Test</title></head><body><h1>Hi</h1></body></html>"
        url = "https://example.com"
        httpx_mock.add_response(url=url, status_code=200, text=html)

        async with httpx.AsyncClient() as client:
            result = await fetch_one(client=client, url=url)

        assert result.status == FetchStatus.OK
        assert result.http_code == 200
        assert result.error is None
        assert result.content is not None
        assert result.content.title == "Test"
        assert "Hi" in result.content.headings
        assert result.elapsed_ms > 0

    # 使用 parametrize 参数化各个场景
    @pytest.mark.parametrize("status_code", [401, 403, 404, 501, 502, 503])
    async def test_one_error_code(self, httpx_mock: HTTPXMock, status_code):
        """单个 抓取失败：4xx、5xx场景"""

        url = "https://example.com/missing"
        httpx_mock.add_response(
            url=url,
            status_code=status_code,
            text="Not Found",
        )

        async with httpx.AsyncClient() as client:
            result = await fetch_one(client=client, url=url)

        assert result.status == FetchStatus.HTTP_ERROR
        assert result.http_code == status_code
        assert result.content is None

    @pytest.mark.parametrize(
        "exception, status, error",
        [
            (httpx.TimeoutException("timed out"), FetchStatus.TIMEOUT, "timed out"),
            (
                httpx.ConnectError("connection refused"),
                FetchStatus.NETWORK_ERROR,
                "connection refused",
            ),
            (httpx.HTTPError("http error"), FetchStatus.HTTP_ERROR, "http_error"),
        ],
    )
    async def test_one_error_connect(self, httpx_mock: HTTPXMock, exception, status, error):
        """单个 抓取失败：超时、网络连接错误"""

        url = "https://example.com"
        httpx_mock.add_exception(exception=exception, url=url)

        async with httpx.AsyncClient() as client:
            result = await fetch_one(client=client, url=url)

        assert result.status == status
        assert result.content is None
        assert error in result.error.lower()

    # @patch mock了某个函数 async_crawler/fetcher/parse_html函数
    # patch的路径是使用这个函数的路径：fetcher/parse_html函数, parse_html函数在fetcher.py使用了
    @patch("async_crawler.fetcher.parse_html")
    async def test_one_parse_error(self, mock_parse, httpx_mock):
        """单个 抓取成功，解析失败"""

        mock_parse.side_effect = ValueError("simulated parse failure")

        html = "<html><head><title>Test</title></head><body><h1>Hi</h1></body></html>"
        url = "https://example.com"
        httpx_mock.add_response(url=url, status_code=200, text=html)

        async with httpx.AsyncClient() as client:
            result = await fetch_one(client=client, url=url)

        assert result.status == FetchStatus.PARSE_ERROR
        assert result.url == url
        assert result.http_code == 200
        assert result.content is None

        # 验证 mock的函数 被调用了1次
        mock_parse.assert_called_once()


class TestFetchMany:
    async def test_many_all_success(self, httpx_mock: HTTPXMock):
        """并发 都成功"""

        base_url = "https://example.com"
        urls = [f"{base_url}/{i}" for i in range(5)]
        for i, url in enumerate(urls):
            httpx_mock.add_response(
                url=url,
                status_code=200,
                text=f"<html><head><title>Page {i}</title></head><body></body></html>",
            )

        results = await fetch_many(urls=urls, concrurrency=3)

        assert len(results) == 5
        for i, res in enumerate(results):  # 验证返回结果的顺序
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
