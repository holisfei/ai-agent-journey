# pyproject.toml

python的工程配置文件，大概分为2类：
- 项目本身的配置信息
- 工具的配置信息

```py
# 集中管理依赖
[project]
name = "my-awesome-tool"
version = "0.1.0"
dependencies = ["httpx", "loguru"]

# ruff 配置
[tool.ruff]
line-length = 120

# 测试框架 pytest 的配置
[tool.pytest.ini_options]
testpaths = ["tests"]
```

# ruff

Ruff 是一个用 Rust 语言编写的 Python 代码检查工具。

在 Ruff 出现之前，Python 开发者通常需要同时安装 flake8（查代码错误）、isort（自动整理 import 顺序）、black（自动格式化代码）等多个工具。而 Ruff 的目标是用这一个工具，极速替代掉上面所有的工具。
它的特点就是快（比传统 Python 写的工具快几十到上百倍），并且功能极其强大：
- 查错：发现你代码里未使用的变量、拼写错误、不符合规范的地方。
- 格式化：一键把你的代码排版得整整齐齐（和 black 效果一样）。
- 自动修复：很多小毛病它不仅能指出来，还能自动帮你改好。

```bash
# 安装
uv add --dev ruff

# 格式化整个项目（会修改文件）
uv run ruff format .

# 只检查不修改
uv run ruff format --check .

# lint 检查
uv run ruff check .

# lint 检查并自动修复能修的问题
uv run ruff check --fix .
```

 Ruff有扩展工具（Astral 官方），会在保存文件时自动 format + 提示 lint 错误

# Pre-commit Hooks

Pre-commit Hooks（预提交钩子）是 Git 版本控制系统中的一个自动化脚本机制。

它的作用是：在你执行 git commit 把代码提交到仓库之前，自动触发一系列的检查。 如果检查没通过，Git 就会直接拒绝你的提交，逼着你把问题修好

安装：
```bash
uv add --dev pre-commit
```

在根目录创建 .pre-commit-config.yaml 文件:
```yaml
repos:
  # 一些通用检查
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace        # 去除行尾空格
      - id: end-of-file-fixer           # 文件末尾确保换行
      - id: check-yaml                  # 检查 YAML 语法
      - id: check-added-large-files     # 拒绝超大文件
      - id: check-merge-conflict        # 检查合并冲突标记

  # ruff
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  # mypy（可选，初学者可以先不加）
  # - repo: https://github.com/pre-commit/mirrors-mypy
  #   rev: v1.13.0
  #   hooks:
  #     - id: mypy
```

激活：
这条命令会在你的 .git/hooks/pre-commit 装一个钩子。从此 git commit 时自动跑检查。
```bash
uv run pre-commit install
```

如果某次你急着提交，想跳过 pre-commit：
```bash
git commit -m "wip" --no-verify
```

# CLI 框架 Typer

Typer 是目前 Python 生态中最流行、最现代化的命令行（CLI）框架。它最大的亮点就是由 FastAPI 的作者开发，因此继承了 FastAPI 极其优雅的 API 设计风格——你只需要会写带类型提示的 Python 函数，就能自动生成专业的命令行工具

定义一个 CLI：
```py
import typer
from loguru import logger

app = typer.Typer(help="异步爬虫 CLI 工具")

@app.command()
def fetch(
    url: str = typer.Argument(..., help="要抓取的 URL"),
    concurrency: int = typer.Option(5, "--concurrency", "-c", help="并发数"),
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
```

使用CLI：
```bash
uv run python src/async_crawler/cli.py --help
uv run python src/async_crawler/cli.py fetch --help
uv run python src/async_crawler/cli.py fetch https://xxx.com -c 10 -v
uv run python src/async_crawler/cli.py version
```

在 pyproject.toml 里加：
```toml
[project.scripts]
mycrawler = "async_crawler.cli:app"

[tool.hatch.build]
packages = ["src/async_crawler"]
```

这样这个cli就是一个真正的命令行工具了：
```bash
uv sync
uv run mycrawler --help
uv run mycrawler fetch https://example.com -c 10
```

# [project.scripts]

uv 把 Python 项目分成两类:
- Application（应用）:自己跑的代码，不发布给别人用数据分析脚本、内部工具,不支持 project.scripts
- Package（包）：Package（包）要被 pip install 安装的库或 CLI 工具httpx、pydantic、ruff，支持 project.scripts

[project.scripts] 的作用是「把某个 Python 函数注册成系统命令」—— 这是 Package 才能做的事，因为系统要把你的代码「安装」进去（包括把你的代码拷贝到 .venv/lib/site-packages/，并生成 .venv/bin/mycrawler 这个可执行文件）。

iOS 类比：
- Application = 你随手写的一个 Playground 文件，能跑，但没法安装到别人手机上
- Package = 你打包成 .framework 或 SPM 包，能被其他项目 import，也能被发布

把项目升级为 Package：
在 pyproject.toml 里加这两段。第一段告诉 uv「我是 Package」：
```toml
[tool.uv]
package = true
```

告诉 Python 怎么打包你的代码（这是标准的打包系统声明）：
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

然后再跑：```uv sync```进行安装命令行

### 注意点：

```__init__.py``` 必须存在:
- iOS 类比：相当于 SPM Package 必须有 Package.swift 才被识别

src 布局需要告诉 hatchling 包在哪:
```toml
[tool.hatch.build]
packages = ["src/async_crawler"]
```





# 工具全景

```py
┌─────────────────────────────────────────────────────┐
│  你写代码                                             │
│  ↓                                                   │
│  保存文件 → VS Code 的 ruff 插件自动格式化、提示错误       │
│  ↓                                                   │
│  本地跑 → uv run python xxx.py（Typer 命令行入口）       │
│  ↓                                                   │
│  git commit → pre-commit 拦截，跑 ruff + 其他检查       │
│  ↓                                                   │
│  git push → GitHub Actions 再跑一次（双保险）           │
└─────────────────────────────────────────────────────-┘

  Typer       = 让代码「可执行」（变成 CLI 命令）
  ruff        = 让代码「干净」（格式 + lint）
  pre-commit  = 让 ruff 等检查「在 commit 前自动跑」
  pyproject   = 所有工具的「中央配置文件」
```

# Anki 卡片

```py
# Typer
- 是什么：把 Python 函数转换为 CLI 命令的库
- 解决什么：argparse 太啰嗦、没类型校验、文档要手写
- 核心：@app.command() + 类型注解 = 自动生成 CLI

# ruff
- 是什么：Rust 写的格式化 + lint 工具
- 解决什么：替代 black/isort/flake8 等一堆工具，统一且快
- 核心：ruff format 格式化，ruff check 查错

# pre-commit
- 是什么:git commit 时自动跑检查的工具
- 解决什么：避免烂代码进入仓库；保证团队风格统一
- 核心:.pre-commit-config.yaml + pre-commit install
```
