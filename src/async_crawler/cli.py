import typer
from loguru import logger

app = typer.Typer(help="异步爬虫 CLI 工具")


@app.command()
def fetch(
    url: str = typer.Argument(..., help=""),
    concurrency: int = typer.Option(5, "--concurrency", "-c", help="并发数量"),
    output: str = typer.Option("result.json", "--output", "-o", help="输出文件"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="详细日志"),
):
    """抓取指定 URL"""
    if verbose:
        logger.info(f"开始抓取 {url}, 并发 {concurrency}")
    typer.echo(f"假装抓了 {url}, 结果保存到 {output}")


@app.command()
def version():
    """显示版本号"""
    typer.echo("async-crawler v0.1.0")


if __name__ == "__main__":
    app()
