# conftest.py - 参数注入 fixture 的「共享空间」

@pytest.fixture 装饰的函数,提供测试数据/对象。但有一个问题:full_html、minimal_html 这种 fixture 是写在 test_parser.py 里,在 test_fetcher.py 里用不到。

conftest.py 解决这个——它是 pytest 的"魔法"文件,放在测试目录下,里面的 @pytest.fixture函数 自动被同目录及子目录所有测试文件共享,不需要 import。

同目录和子目录的测试函数参数直接使用@pytest.fixture的函数就行

```py
def test_title(sample_html):              # ← 直接当参数,pytest 自动注入
    result = parse_html(sample_html)
    assert result.title == "Sample Page"
```

# @pytest.fixture 参数注入 - scope 与 yield

默认每个测试都会重新创建一次 fixture(scope="function")。但有些 fixture 创建成本高(开数据库连接、启动服务、加载大文件),不该每次都建。

```py
@pytest.fixture(scope="function")   # 默认,每个测试函数前后都 setup/teardown
def quick(): ...

@pytest.fixture(scope="module")     # 整个测试文件共用一份
def db_connection(): ...

@pytest.fixture(scope="session")    # 整个 pytest 跑期间只创建一份
def expensive_resource(): ...
```

### yield - setup + teardown 一体化

如果 fixture 需要「准备 + 清理」(开了文件要关、连了数据库要断),用 yield:

```py
@pytest.fixture
def tmp_file(tmp_path): # tmp_path 是 pytest 内置 fixture——给你一个临时目录,测试结束自动删。
    file = tmp_path / "test.txt"
    file.write_text("hello")
    yield file              # ← 测试函数拿到的是 file
    # yield 之后是清理代码
    if file.exists():
        file.unlink()
```

# parametrize - 参数化

@pytest.mark.parametrize 可以让一个测试函数自动跑多个参数里的场景

### @pytest.mark.parametrize + id 让测试名好看

```py
@pytest.mark.parametrize("html, expected_title", [
    pytest.param(
        "<html><head><title>Hello</title></head><body></body></html>",
        "Hello",
        id="normal",
    ),
    pytest.param(
        "<html><head><title>  Spaced  </title></head><body></body></html>",
        "Spaced",
        id="strips_whitespace",
    ),
    pytest.param(
        "<html><body></body></html>",
        None,
        id="missing_title",
    ),
])
def test_title_extraction(html, expected_title):
    result = parse_html(html)
    assert result.title == expected_title
```

### 堆叠 parametrize = 笛卡尔积

```py
@pytest.mark.parametrize("status_code", [200, 301, 302])
@pytest.mark.parametrize("method", ["GET", "POST"])
def test_combinations(status_code, method):
    ...
```
自动产生 3 × 2 = 6 个测试用例。所有 status_code 和 method 的组合都被测了

# mock.patch - 替换「依赖」

把测试代码里的某个「外部依赖」替换成可控的假货,让测试可重复、快、不依赖外部世界。
pytest-httpx 已经在做 mock(替换了 httpx)。

Python 标准库的 unittest.mock.patch——更通用,任何对象都能 mock。

```py
from unittest.mock import patch

@patch("async_crawler.fetcher.parse_html")    # 注意路径!详见下文
async def test_parse_error(mock_parse, httpx_mock):
    # mock_parse 是 parse_html 的"替身",可以指定它的行为
    mock_parse.side_effect = ValueError("simulated parse failure")

    httpx_mock.add_response(url="https://x.com", status_code=200, text="any")

    async with httpx.AsyncClient() as client:
        result = await fetch_one(client, "https://x.com")

    assert result.status == FetchStatus.PARSE_ERROR
    assert "simulated parse failure" in result.error
```

### @patch() 的路径 -「被使用的地方」,不是「被定义的地方」

```py
parser.py            ← parse_html 定义在这
fetcher.py           ← 在这里 from parser import parse_html,然后使用
```

@patch()的路径函数是在哪里用的路径，而不是被声明定义的路径

### mock 对象的两种行为控制

```py
# 方式 A: return_value——指定返回什么
mock_parse.return_value = PageContent(title="fake", ...)

# 方式 B: side_effect——指定"调用时发生什么"
mock_parse.side_effect = ValueError("boom")   # 调用时抛异常
mock_parse.side_effect = [page1, page2, page3]  # 依次返回这些值
mock_parse.side_effect = lambda html: PageContent(title=f"mocked-{len(html)}")  # 自定义函数
```
### @patch() 参数顺序的完整规则

@patch 装饰器注入的 mock 参数,必须紧跟在 self/cls 之后,在 pytest fixture 参数之前。

多个 @patch 堆叠时,最靠近函数的 @patch 注入第一个 mock 参数(从内往外)。

单个patch：
```py
class TestX:
    @patch("module.func")
    def test_x(self, mock_func, fixture_a, fixture_b):
               #         ↑          ↑          ↑
          #         patch 注入   pytest 注入  pytest 注入
```

多个@patch(从下往上注入)：
```py
class TestX:
    @patch("module.func_a")     # 最外层,最后一个注入
    @patch("module.func_b")     # 最内层,最先注入
    def test_x(self, mock_b, mock_a, fixture):
              #         ↑      ↑       ↑
             #         自下而上注入    pytest 注入
```

### 验证 mock 是否被调用、怎么被调用

```py
# 测试代码里...
result = await fetch_one(client, "https://x.com")

# 断言 mock 被调用过、参数对
mock_parse.assert_called_once()              # 被调用了恰好 1 次
mock_parse.assert_called_with("<html>...")  # 用这个参数被调用过
mock_parse.call_count                        # 被调用了几次
mock_parse.call_args                         # 上次调用的参数
```

### 把 mock 写进 with 块

@patch() 装饰器适合「整个测试函数都需要 mock」。如果只想在部分代码块里 mock,用 with:

```py
async def test_xxx(httpx_mock):
    httpx_mock.add_response(url="...", ...)

    with patch("async_crawler.fetcher.parse_html") as mock_parse:
        mock_parse.side_effect = ValueError("boom")
        # 只在这个 with 块里 parse_html 被 mock 了
        ...

    # with 块外恢复正常
```

### 行为写进 @patch

```py
@patch("async_crawler.fetcher.parse_html", side_effect=ValueError("malformed html"))
async def test_xxx(self, mock_parse, httpx_mock):
```

# 测试覆盖率

```bash
uv run pytest --cov=async_crawler --cov-report=term-missing
```

--cov-report=term-missing 会列出没覆盖的行号。

### 生成 HTML 报告(更直观)

```bash
uv run pytest --cov=async_crawler --cov-report=html
open htmlcov/index.html
```

### 在 pyproject.toml 配置覆盖率

```toml
[tool.coverage.run]
source = ["src/async_crawler"]
omit = ["*/tests/*", "*/_try_*.py"]    # 排除测试文件本身和临时调试脚本

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if __name__ == .__main__.:",
    "raise NotImplementedError",
]
show_missing = true                     # 默认显示 missing
fail_under = 80                          # 覆盖率低于 80% 时 pytest 失败
```

# Anki 卡片

```py
Q: pytest 自动共享 fixture 的文件叫什么?
A: conftest.py,放在测试目录下,自动加载

Q: fixture 怎么做"setup + teardown"?
A: 用 yield。yield 前 setup,yield 后 teardown

Q: pytest 内置的临时目录 fixture?
A: tmp_path,测试结束自动清理

Q: parametrize 给每组测试起名?
A: pytest.param(v1, v2, id="名字")

Q: 堆叠多个 parametrize 装饰器?
A: 笛卡尔积,所有组合都被测

Q: mock.patch 的路径写哪?
A: 写"被使用的地方",不是"被定义的地方"。from x import y 后,patch 的是 当前模块.y

Q: 让 mock 抛异常?
A: mock.side_effect = ExceptionClass("msg")

Q: 让 mock 返回固定值?
A: mock.return_value = ...

Q: 让 mock 多次返回不同值?
A: mock.side_effect = [v1, v2, v3]

Q: 验证 mock 被调用过?
A: mock.assert_called_once() / assert_called_with(...) / call_count

Q: 看覆盖率细节(哪行没测)?
A: pytest --cov=包 --cov-report=term-missing
   或 --cov-report=html 生成 HTML

Q: 设定覆盖率门槛?
A: pyproject.toml [tool.coverage.report] fail_under = 80
```
