import asyncio
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

from async_crawler.fetcher import fetch_many_process
from async_crawler.models import FetchStatus, PageResult

app = typer.Typer(help="异步爬虫 CLI 工具")
console = Console()


@app.command()  # Annotated[原始类型, 备注信息1, 备注信息2, ...]
def fetch(
    urls: Annotated[list[str] | None, typer.Argument(help="要抓取的URL")] = None,
    file: Annotated[str | None, typer.Option("--file", "-f", help="从文件读 URL")] = None,
    concurrency: Annotated[int, typer.Option("--concurrency", "-c", help="并发数量")] = 5,
    timeout: Annotated[float, typer.Option("--timeout", "-t", help="超时(秒)")] = 15.0,
    output: Annotated[str, typer.Option("--output", "-o", help="输出文件")] = Path("result.json"),
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
        console.print("[red]错误:[/red] 没有可抓取的urls")
        console.print("请使用: mycrawler fetch URL1 URL2 ... 或者 --file 文件")
        raise typer.Exit(code=1)

    console.print(
        f"[bold]任务执行中... 数量:{len(url_list)} Urls[/bold] (并发:{concurrency},超时:{timeout})"
    )

    # 2. 跑爬虫 + 显示进度
    start = datetime.now()
    results = asyncio.run(
        _run_with_progress(urls=url_list, concrurrency=concurrency, timeout=timeout)
    )
    elapsed = (datetime.now() - start).total_seconds()

    # 3. 输出表格统计
    _print_summary(results=results, elapsed=elapsed)

    # 4. 将解析的结果写入文件
    _write_to_file(results=results, output=Path(output), elapsed=elapsed)
    console.print(f"\n💾 保存到了[cyan]{output}[/cyan]")


# 任务进度
async def _run_with_progress(urls, concrurrency, timeout) -> list[PageResult]:
    """跑爬虫,用 rich.Progress 显示进度"""
    with Progress(
        SpinnerColumn(),  # loading
        TextColumn("[progress.description]{task.description}"),  # 文本，任务描述
        BarColumn(),  # 进度条
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),  # 文本，百分百
        TextColumn("•"),
        TextColumn("{task.completed}/{task.total}"),  # 文本，完成的任务/总任务
        TextColumn("•"),
        TimeElapsedColumn(),  # 已经花费的时间
        TextColumn(" | "),
        console=console,
    ) as process:
        # 生成总任务 task_id
        task_id = process.add_task("任务执行中...", total=len(urls))

        # 更新子任务的回调实现
        def on_progress(_: PageResult) -> None:
            process.update(task_id=task_id, advance=1)

        return await fetch_many_process(
            urls=urls, concrurrency=concrurrency, timeout=timeout, on_progress=on_progress
        )


# 表格统计
def _print_summary(results: list[PageResult], elapsed: float) -> None:
    """打印统计摘要表格"""
    stats = Counter(res.status for res in results)  # 获取所有状态list
    total = len(results)
    ok_count = stats.get(FetchStatus.OK, 0)  # 统计状态是OK的数量

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
    table.add_row(
        "[green]成功[/green]", f"{ok_count} ({ok_count/total*100:.0f}%)" if total else "0"
    )
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
        "results": [m.model_dump(mode="json") for m in results],
    }
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


@app.command()
def version():
    """显示版本号"""
    typer.echo("async-crawler v0.1.0")


if __name__ == "__main__":
    app()
