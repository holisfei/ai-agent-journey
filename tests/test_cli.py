import json
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from async_crawler.cli import app
from async_crawler.models import FetchStatus, PageContent, PageResult

runner = CliRunner()


# 参数注入
@pytest.fixture
def take_results() -> list[PageResult]:
    """假的爬虫结果,跳过真实网络"""
    return [
        PageResult(
            url="https://www.a.com",
            status=FetchStatus.OK,
            http_code=200,
            elapsed_ms=120,
            content=PageContent(title="Page A"),
        ),
        PageResult(
            url="https://www.b.com",
            status=FetchStatus.HTTP_ERROR,
            http_code=404,
            elapsed_ms=80,
        ),
    ]


class TestFetchCommand:
    def test_no_urls_exits_with_error(self):
        """测试不传参数"""
        result = runner.invoke(app, ["fetch"])  # 不传 -file 参数
        assert result.exit_code == 1  # 验证 异常
        assert "没有可抓取的urls" in result.output  # 验证 输出文案

    def test_nonexistent_file_exits_with_error(self):
        """测试文件不存在"""
        result = runner.invoke(app, ["fetch", "--file", "no_such_file.txt"])
        assert result.exit_code == 1
        assert "未找到" in result.output

    def test_success_writes_json(self, tmp_path, take_results):
        """mock函数fetch_many_process, 验证 CLI 流程"""
        # 测试用临时路径
        output: Path = tmp_path / "out.json"

        # mock函数：将抓取逻辑替换成mock的逻辑：根据参数返回解析的结果，期间触发子任务的回调
        async def fetch_many_mock(urls, **kwargs):
            # 拿到原函数的回调
            on_progress_call = kwargs.get("on_progress")
            # 根据假数据 触发进度回调
            for r in take_results:
                if on_progress_call:
                    on_progress_call(r)
            # 返回假数据
            return take_results

        # mock 了 fetch_many_process函数逻辑
        with patch("async_crawler.cli.fetch_many_process", side_effect=fetch_many_mock):
            result = runner.invoke(
                app, ["fetch", "https://www.a.com", "https://www.b.com", "-o", str(output)]
            )

        assert result.exit_code == 0
        assert output.exists()

        # 写入文件的假数据
        data: dict = json.loads(output.read_text())
        assert data["metadata"]["total"] == 2
        assert len(data["results"]) == 2
        assert data["results"][0]["url"] == "https://www.a.com"
        assert data["results"][0]["status"] == FetchStatus.OK
        assert data["results"][1]["url"] == "https://www.b.com"
        assert data["results"][1]["status"] == FetchStatus.HTTP_ERROR

    def test_file_exits(self, tmp_path, take_results):
        """测试从文件读取urls"""
        input_file: Path = tmp_path / "urls.txt"
        input_file.write_text("https://www.a.com\nhttps://www.b.com\n")
        output_file: Path = tmp_path / "output.json"

        async def fetch_many_mock(urls, **kwargs):
            assert list(urls) == ["https://www.a.com", "https://www.b.com"]
            return take_results

        with patch("async_crawler.cli.fetch_many_process", side_effect=fetch_many_mock):
            result = runner.invoke(
                app, ["fetch", "--file", str(input_file), "--output", str(output_file)]
            )

        assert result.exit_code == 0
