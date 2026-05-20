# rich

rich 是 Python 圈最知名的 CLI 美化库。所有现代 Python CLI(Typer、pip、uv、Textual)都用 rich 渲染输出。

```bash
uv add rich
```

### Console、Progress、Table

3 个核心组件,其他用到再查文档(rich 功能极多,初学者最容易在里面迷失)。

#### 1. Console:替代 print 的彩色输出

console.print 就是带彩色 + 自动格式化的 print。日常 print 改成它,代码立刻精致一截。

```py
from rich.console import Console

console = Console()

console.print("Hello", style="bold green")
console.print("[red]Error:[/red] something failed")
console.print({"name": "alice", "age": 30})    # dict 自动美化
```

#### 2. Progress:进度条

关键概念:
- Progress() 是上下文管理器
- add_task(描述, total=总量) 加一个任务条
- update(task, advance=N) 推进 N 步

```py
from rich.progress import Progress

Progress() 的 UI 其实非常灵活，它就像搭积木一样，由一个个“列（Columns）”拼接而成。你可以根据自己的需求，自由组合出想要的进度条长相。

[任务描述] [进度条本身] [百分比] [已完成的数量/总数量] [剩余时间/总耗时]

with Progress(
    SpinnerColumn(),  # 旋转的小菊花加载动画
    TextColumn("•")   # 任意文字
    TextColumn("[progress.description]{task.description}"),  # 任务描述（比如“正在下载...”)
    BarColumn(bar_width=40),  # 进度条本体（可以设置宽度）
    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),  # 百分比显示
    TimeElapsedColumn(),  # 已经花费的时间
    TimeRemainingColumn(),  # 预计剩余的时间
) as progress:
    task = progress.add_task("Crawling", total=100)
    for i in range(100):
        # 干活
        progress.update(task, advance=1)
```


#### 3. Table:漂亮的表格

```py
from rich.table import Table

table = Table(title="Summary")
table.add_column("Metric")
table.add_column("Value", justify="right")
table.add_row("Total", "100")
table.add_row("Success", "87")

console.print(table)
```

# 爬虫任务对外回调

将爬虫的任务回调，每完成一个，对外回调一个，使用 as_completed，并发执行任务

 as_completed并发执行任务，子任务完成后都会返回结果，然后使用闭包函数回调出去，这样只是新增了一个回调闭包，函数返回值没有变化

```py
async def fetch_many_process(
    urls: Sequence[str],
    concrurrency: int = 5,
    timeout: float = 15,
    on_progress: Callable[[PageResult], None] | None = None
) -> list[PageResult]:
    """
    批量并发抓取 URL。
    用 Semaphore 限流,用 as_completed 管理生命周期。
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
        # as_completed，并发执行任务，执行结果一个一个返回
        tasks = [asyncio.create_task(_bounded_fetch(client=client, url=url)) for url in urls]
        results: list[PageResult] = []
        for task in asyncio.as_completed(tasks):
            result = await task
            results.append(result)
            # 每完成一个任务，回调出去，告诉外部当前的进度
            if on_progress is not None:
                on_progress(result)
    return results
```

# cli 命令行格式化输出

```py
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Annotated

import typer
from loguru import logger
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.table import Table
from collections import Counter

from async_crawler.fetcher import fetch_many_process
from async_crawler.models import FetchStatus, PageResult

app = typer.Typer(help="异步爬虫 CLI 工具")
console = Console()


@app.command() # Annotated[原始类型, 备注信息1, 备注信息2, ...]
def fetch(
    urls: Annotated[list[str] | None, typer.Argument(help="要抓取的URL")] = None,
    file: Annotated[Path | None, typer.Option("--file", "-f", help="从文件读 URL")] = None,
    concurrency: Annotated[int, typer.Option("--concurrency", "-c", help="并发数量")] = 5,
    timeout: Annotated[float, typer.Option("--timeout", "-t", help="超时(秒)")] = 15.0,
    output: Annotated[Path, typer.Option("--output", "-o", help="输出文件")] = Path("result.json"),
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="详细日志")] = False,
):
    """批量异步抓取 URL,提取标题/描述/链接等"""

    # 1. 收集待抓取的urls
    url_list: list[str] = list(urls) if urls else []
    if file:
        from_file: Path = Path(file)
        if not from_file.exists():
            console.print(f"[red]错误:[/red] 文件 {from_file} 未找到")
            raise typer.Exit(code=1)
        url_list.extend(line.strip() for line in from_file.read_text().splitlines() if line.strip())

    if not url_list:
        console.print(f"[red]错误:[/red] 没有可抓取的urls")
        console.print(f"请使用: mycrawler fetch URL1 URL2 ... 或者 --from-file urls.txt")
        raise typer.Exit(code=1)

    console.print(f"[bold]任务执行中... {len(url_list)} Urls[/bold] (concurrency={concurrency}, timeout={timeout})")

    # 2. 跑爬虫 + 显示进度
    start = datetime.now()
    results = asyncio.run(_run_with_progress(urls=url_list, concrurrency=concurrency, timeout=timeout))
    elapsed = (datetime.now() - start).total_seconds()

    # 3. 输出表格统计
    _print_summary(results=results, elapsed=elapsed)

    # 4. 将解析的结果写入文件
    _write_to_file(results=results, output=output, elapsed=elapsed)
    console.print(f"\n💾 保存到了[cyan]{output}[/cyan]")

# 任务进度
async def _run_with_progress(urls, concrurrency, timeout) -> list[PageResult]:
    """跑爬虫,用 rich.Progress 显示进度"""
    with Progress(
        SpinnerColumn(), # loading
        TextColumn("[progress.description]{task.description}"), # 文本，任务描述
        BarColumn(), # 进度条
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),  # 文本，百分百
        TextColumn("•"),
        TextColumn("{task.completed}/{task.total}"), # 文本，完成的任务/总任务
        TextColumn("•"),
        TimeElapsedColumn(), # 已经花费的时间
        TextColumn(" | "),
        console=console,
    ) as process:
        # 生成总任务 task_id
        task_id = process.add_task("任务执行中...", total=len(urls))
        # 更新子任务的回调实现
        def on_progress(_: PageResult) -> None:
            process.update(task_id=task_id, advance=1)
        return await fetch_many_process(urls=urls, concrurrency=concrurrency, timeout=timeout, on_progress=on_progress)

# 表格统计
def _print_summary(results: list[PageResult], elapsed: float) -> None:
    """打印统计摘要表格"""
    stats = Counter(res.status for res in results) # 获取所有状态list
    total = len(results)
    ok_count = stats.get(FetchStatus.OK, 0) # 统计状态是OK的数量

    # 平均耗时
    if total > 0:
        avg_ms = sum(res.elapsed_ms for res in results) / total
    else:
        avg_ms = 0

    # 创建表格
    table = Table(title="摘要", show_header=True)
    # 2列
    table.add_column("指标", style="dim")
    table.add_column("值", justify="right")
    # 每一行的内容
    table.add_row("总计", str(total))
    table.add_row("[green]成功[/green]", f"{ok_count} ({ok_count/total*100:.0f}%)" if total else "0")
    table.add_row("[yellow]HTTP错误[/yellow]", str(stats.get(FetchStatus.HTTP_ERROR, 0)))
    table.add_row("[yellow]超时[/yellow]", str(stats.get(FetchStatus.TIMEOUT, 0)))
    table.add_row("[red]网络错误[/red]", str(stats.get(FetchStatus.NETWORK_ERROR, 0)))
    table.add_row("[red]解析错误[/red]", str(stats.get(FetchStatus.PARSE_ERROR, 0)))
    table.add_row("总耗时", f"{elapsed:.2f}s")
    table.add_row("平均耗时", f"{avg_ms:.2f}s")

    console.print()
    console.print(table)

def _write_to_file(results: list[PageResult], output: Path, elapsed: float) -> None:
    """把结果写入 JSON 文件"""
    payload = {
        "metadata": {
            "total": len(results),
            "elapsed_seconds": round(elapsed),
            "generated_at": datetime.now().isoformat(),
        },
        "results": [m.model_dump(mode="json") for m in results]
    }
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


@app.command()
def version():
    """显示版本号"""
    typer.echo("async-crawler v0.1.0")


if __name__ == "__main__":
    app()
```

运行：```uv run mycrawler fetch --file urls.txt -c 3```

### Annotated

Typer 的现代写法:Annotated(Annotated[类型，cli配置备注说明]), Typer 0.9+ 推荐的写法——把"类型注解"和"CLI 配置"分开

### model_dump(mode="json")

Pydantic 的model转json方法 model_dump() 默认会保留 Python 原生类型(datetime 还是 datetime 对象、Enum 还是 enum 对象)。mode="json"参数是告诉 Pydantic: 把这些都转成 JSON 兼容的基本类型(datetime → ISO 字符串, Enum → 字符串)。

### JSON 输出的元数据 wrapper

不要直接输出数组,要加 metadata 外层摘要字段。原因:

- 数据消费者可以一眼看到"什么时候跑的、耗时多少"
- 未来加新字段(版本号、配置项、统计摘要)有地方放,不破坏 API

### typer.Exit

不要用 sys.exit(1) 或 exit(1),

typer.Exit 是 Typer 专门提供的,行为更优雅(支持测试时拦截)。code=1 是非 0 退出码,在 Shell 脚本和 CI 里能被检测到。

### ensure_ascii=False

```json.dumps(payload, ensure_ascii=False, indent=2)```

默认 json.dumps 会把所有非 ASCII 字符转成 \uXXXX(中文也是)。ensure_ascii=False 让中文等字符保留原样,文件可读性更高。

# cli 的测试 CliRunner

CLI 测试和单元测试逻辑不同——测试整个命令的行为,不是单个函数。Typer 有专门的工具。

```py
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
        result = runner.invoke(app, ["fetch"]) # 不传 -file 参数
        assert result.exit_code == 1 # 验证 异常
        assert "没有可抓取的urls" in result.output # 验证 输出文案

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
            result = runner.invoke(app, ["fetch", "https://www.a.com", "https://www.b.com", "-o", str(output)])

        assert result.exit_code == 0
        assert output.exists()

        # 写入文件的假数据
        data:dict = json.loads(output.read_text())
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
            assert list(urls) == ["https://www.a.com","https://www.b.com"]
            return take_results

        with patch("async_crawler.cli.fetch_many_process", side_effect=fetch_many_mock):
            result = runner.invoke(app, ["fetch", "--file", str(input_file), "--output", str(output_file)])

        assert result.exit_code == 0
```

Typer 测试的几个关键点:

### CliRunner 是核心

```bash
runner = CliRunner()
result = runner.invoke(app, ["fetch", "url1", "-c", "5"])
```

它像真实终端那样调用你的 CLI,但捕获输出、不实际进程退出,可断言。

返回的 result:
- result.exit_code:退出码(0 成功,非 0 失败)
- result.output:stdout 内容
- result.exception:如果挂了,异常对象

### mock 异步函数

```py
async def fetch_many_mock(urls, **kwargs):
    return fake_results

with patch("async_crawler.cli.fetch_many", side_effect=fake_fetch_many):
    ...
```
注意:
- patch路径是使用函数的路劲：cli.fetch_many_process。
- side_effect 接受 async 函数也 OK, 调用时返回协程 coroutine, CLI 里 asyncio.run 会跑它。

# Anki 卡片

```py
Q: Python 圈最知名的命令行美化库?
A: rich, Typer/pip/uv 都在用

Q: rich 的三大核心组件?
A: Console (彩色 print)、Progress (进度条)、Table (表格)

Q: 进度条 + asyncio 怎么配合?
A: 用 as_completed 替代 TaskGroup,"完成一个就推进一格"

Q: as_completed 和 TaskGroup 的取舍?
A: TaskGroup 等全部完成,有错误自动取消;as_completed 边完成边处理,适合进度条/流式

Q: Pydantic 序列化为 JSON 兼容类型?
A: model_dump(mode="json"),把 datetime/Enum 转成字符串

Q: Typer 测试用什么?
A: typer.testing.CliRunner,模拟终端调用,捕获 exit_code/output

Q: Typer 退出时报错怎么写?
A: raise typer.Exit(code=1), 不要 sys.exit
```
