import httpx
from pytest_httpx import HTTPXMock

from async_crawler.fetcher import fetch_many, fetch_one
from async_crawler.models import FetchStatus


class TestFetchOne:
    async def test_one_success(self, httpx_mock: HTTPXMock):
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
        httpx_mock.add_response(url=url, status_code=500)

        async with httpx.AsyncClient() as client:
            result = await fetch_one(client=client, url=url)

        assert result.status == FetchStatus.HTTP_ERROR
        assert result.http_code == 500

    async def test_one_timeout(self, httpx_mock: HTTPXMock):
        """超时应该被分类为 TIMEOUT"""
        url = "https://example.com"
        httpx_mock.add_exception(exception=httpx.TimeoutException("timed out"), url=url)

        async with httpx.AsyncClient() as client:
            result = await fetch_one(client=client, url=url)

        assert result.status == FetchStatus.TIMEOUT
        assert result.content is None
        assert "timed out" in result.error.lower()

    async def test_one_connection_error(self, httpx_mock: HTTPXMock):
        """连接错误应该被分类为 NETWORK_ERROR"""
        url = "https://example.com"
        httpx_mock.add_exception(exception=httpx.ConnectError("connection refused"), url=url)

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
