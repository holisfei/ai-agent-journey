# 网页爬虫
```py
html = """
<html>
  <head><title>Hello World</title></head>
  <body>
    <h1 class="main">Welcome</h1>
    <a href="/about">About us</a>
    <a href="/contact">Contact</a>
    <meta name="description" content="A demo page">
  </body>
</html>
"""

# DOM树
tree = HTMLParser(html=html)

tree.css("a")              # 所有 <a>
tree.css("a.external")     # class 是 external 的 a
tree.css("#main")          # id 是 main 的元素
tree.css("div > p")        # div 的直接子 p
tree.css("div p")          # div 内的所有 p（嵌套也算）
tree.css("a[href]")        # 有 href 属性的 a
tree.css('meta[name="description"]')   # name="description" 的 meta
tree.css("h1, h2, h3")     # 多选

# 找到所有匹配的元素
links = tree.css("a")
# 找到第一个匹配的元素
title = tree.css_first("title")
node_h1 = tree.css_first("h1")
# "Welcome"  ← 元素内文字
# text() 默认会包含改节点下子节点的所有文字,
# 如果只需要本节点的文字（不包含子节点），用 deep=False（默认 True）
node_h1.text(deep=False)
# {"class": "main"}  ← 该标签下的的所有属性dict
node_h1.attributes
 # "main"   ← get取单个属性(安全)，而不是 attributes["class"]
node_h1.attributes.get("class")
# 标签名称 h1
node_h1.tag

```

# pytest

添加依赖： ```uv add --dev pytest```

pytest 的约定：
- 测试文件名 test_*.py 或 *_test.py
- 测试函数名 test_*
- 用普通的 assert 而不是 self.assertEqual（比 Java/iOS 的 unittest 风格简洁得多）

最小的例子：
``` py
# tests/test_simple.py
def test_one_plus_one():
    assert 1 + 1 == 2
```

运行测试: ```uv run pytest```

### 带测试覆盖率测试

添加依赖： ```uv add --dev pytest-cov```
运行测试：
```bash
uv run pytest --cov=async_crawler --cov-report=term-missing
```
会看到每个文件多少行被测试覆盖了

### 关于 pytest 的几个核心概念

#### 1. fixture（夹具）

「测试用的准备好的数据/对象」。用 @pytest.fixture 装饰。测试函数把 fixture 名字作为参数，pytest 自动注入。

```py
@pytest.fixture
def user():
    return User(name="alice")

def test_user_name(user):    # 自动注入 user
    assert user.name == "alice"
```

#### 2. parametrize（参数化）

parametrize 让你「一个测试函数，自动跑多组不同的数据」。

@pytest.mark.parametrize 有两个参数：
- 第一个：字符串 "n, expected"，告诉 pytest「我下面要传入两个值，分别叫 n 和 expected」
- 第二个：列表，每一行是一组数据，顺序对应上面的参数名

```py
@pytest.mark.parametrize("input,expected", [
    ("hello", 5),
    ("", 0),
    ("世界", 2),
])
def test_length(input, expected):
    assert len(input) == expected
```
input列是数输入的册数数据，expected列是期望的测试结果

给每组数据起名字（让报错更清晰）

假设你想测试一个函数 is_even(n)（判断是不是偶数）：
```py
@pytest.mark.parametrize("n, expected", [
    pytest.param(0, True, id="zero"),
    pytest.param(2, True, id="positive_even"),
    pytest.param(3, False, id="positive_odd"),
    pytest.param(-4, True, id="negative_even"),
])
def test_is_even(n, expected):
    assert is_even(n) == expected
```
n列表是具体的所有入参，expected列表是期望的结果，id列表是每一个case的标记名称

#### 3. 分类组织：class 包起来

用 class TestExtractTitle:，把相关测试归类。class 内部写具体的测试用例函数，pytest 自动识别 Test* 开头的类和函数。

#### 4. assert 写法

```py
assert x == 1
assert "hello" in result
assert len(items) > 0
assert obj.field is None
```

失败时 pytest 会智能展示对比

# 示例

解析逻辑：
```py
from selectolax.parser import HTMLParser
from async_crawler.models import Link, PageContent

# ========= 解析统一入口  =========

def parse_html(html:str) -> PageContent:
    """从一个HTML网页解析所有内容"""
    tree = HTMLParser(html=html)
    return PageContent(
        title=_parse_title(tree=tree),
        description=_parse_description(tree=tree),
        headings=_parse_headings(tree=tree),
        links=_parse_links(tree=tree),
        text_length=_parse_length(tree=tree)
    )

# ========== 子解析 ==========

def _parse_title(tree: HTMLParser) -> str | None:
    node = tree.css_first("title")
    return node.text().strip() if node else None

def _parse_description(tree: HTMLParser) -> str | None:
    node = tree.css_first('meta[name="description"]')
    if not node:
        return None
    content = node.attributes.get("content").strip()
    return content if content else None

def _parse_headings(tree: HTMLParser) -> list[str]:
    nodes = tree.css("h1, h2")
    return [node.text().strip() for node in nodes if node.text().strip()]

def _parse_links(tree: HTMLParser) -> list[Link]:
    nodes = tree.css("a[href]")
    links: list[Link] = []
    for node in nodes:
        attributes = node.attributes
        url = attributes.get("href")
        if url:
            link = Link(url=url, text=node.text().strip())
            links.append(link)
    return links

def _parse_length(tree: HTMLParser) -> int:
    body = tree.css_first("body")
    return len(body.text().strip()) if body else 0
```

测试公里逻辑：
```py
import pytest
from async_crawler.parser import parse_html

# ========== 测试 输入 数据 - 可以是各种数据 ==========

@pytest.fixture
def full_html() -> str:
    """一个完整的、字段齐全的 HTML"""
    return """
    <html>
      <head>
        <title>Test Page</title>
        <meta name="description" content="A test description">
      </head>
      <body>
        <h1>Heading 1</h1>
        <h2>Heading 2</h2>
        <a href="/about">About</a>
        <a href="https://example.com">External</a>
        <p>Some text here.</p>
      </body>
    </html>
    """

@pytest.fixture
def minimal_html() -> str:
    """一个极简 HTML，几乎什么都没有"""
    return "<html><body></body></html>"

@pytest.fixture
def nested_html() -> str:
    """一个嵌套的 HTML"""
    return """
    <html>
        <body>
            <div>
                <a href="/about">About</a>
            </div>
        </body>
    </html>
    """

# ========== 测试 用例 -> 测试各个场景 ==========

# title 测试用例

class TestExtractTitle:
    """title 标签的测试"""
    def test_extracts_title(self, full_html):
        result = parse_html(html=full_html)
        assert result.title == "Test Page"

    def test_returns_none_when_no_title(self, minimal_html):
        result = parse_html(minimal_html)
        assert result.title is None

    def test_strips_whitespace_from_title(self):
        html = "<html><head><title>  Spaced Title  </title></head><body></body></html>"
        result = parse_html(html)
        assert result.title == "Spaced Title"

# Description 测试用例

class TestExtractDescription:
    """meta-description的测试"""
    def test_extracts_title(self, full_html):
        result = parse_html(html=full_html)
        assert result.description == "A test description"

    def test_returns_none_when_no_meta(self, minimal_html):
        result = parse_html(minimal_html)
        assert result.description is None

# h 标签测试用例

class TestExtractHeadings:
    """headings 字段的测试"""

    def test_extracts_h1_and_h2(self, full_html):
        result = parse_html(full_html)
        assert result.headings == ["Heading 1", "Heading 2"]

    def test_empty_when_no_headings(self, minimal_html):
        result = parse_html(minimal_html)
        assert result.headings == []

    def test_skips_empty_headings(self):
        html = "<html><body><h1></h1><h1>Real</h1><h2>   </h2></body></html>"
        result = parse_html(html)
        assert result.headings == ["Real"]

# a 标签测试用例

class TestExtractLinks:
    """links 字段的测试"""

    def test_extracts_all_links_with_href(self, full_html):
        result = parse_html(full_html)
        assert len(result.links) == 2
        assert result.links[0].url == "/about"
        assert result.links[0].text == "About"

    def test_skips_links_without_href(self):
        html = '<html><body><a>no href</a><a href="/x">yes</a></body></html>'
        result = parse_html(html)
        assert len(result.links) == 1
        assert result.links[0].url == "/x"

    def test_empty_when_no_links(self, minimal_html):
        result = parse_html(minimal_html)
        assert result.links == []

    def test_nested_with_links(self, nested_html):
        result = parse_html(nested_html)
        assert result.links[0].url == "/about"
        assert result.links[0].text == "About"
```

# Anki 卡片

```py
Q: 爬虫场景最快的 HTML 解析库?
A: selectolax (C 实现，比 lxml 快 2-3 倍)

Q: selectolax 查单个/多个元素?
A: css_first(selector) 返回单个或 None;css(selector) 返回 list

Q: 取节点文字和属性?
A: node.text() 取文字;node.attributes.get("xxx") 取属性

Q: pytest 测试文件和函数命名约定?
A: 文件 test_*.py,函数 test_*

Q: pytest 共享测试数据的机制?
A: @pytest.fixture,作为参数注入测试函数

Q: pytest 一个测试跑多组数据?
A: @pytest.mark.parametrize

Q: 测试覆盖率工具?
A: pytest-cov, uv run pytest --cov=包名
```
