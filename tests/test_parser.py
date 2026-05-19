import pytest

from async_crawler.parser import parse_html

# 输入数据来自conftest.py，不需要导入，输入参数直接使用

full_html_str = """
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

link_html_nohref_str = """
    <html><body><a>no href</a><a href="/x">yes</a></body></html>
"""

nested_html_str = """
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

    @pytest.mark.parametrize(
        "input_html, result_title",
        [
            pytest.param(full_html_str, "Test Page"),
            pytest.param(
                "<html><head><title>  Spaced Title  </title></head><body></body></html>",
                "Spaced Title",
            ),
        ],
    )
    def test_extracts_title(self, input_html, result_title):
        result = parse_html(html=input_html)
        assert result.title == result_title

    def test_returns_none_when_no_title(self, minimal_html):
        result = parse_html(minimal_html)
        assert result.title is None


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
        result = parse_html(link_html_nohref_str)
        assert len(result.links) == 1
        assert result.links[0].url == "/x"
        assert result.links[0].text == "yes"

    def test_empty_when_no_links(self, minimal_html):
        result = parse_html(minimal_html)
        assert result.links == []

    def test_nested_with_links(self, nested_html):
        result = parse_html(nested_html)
        assert result.links[0].url == "/about"
        assert result.links[0].text == "About"


# a标签使用 pytest参数化定义用例


LINKS_CASE = [
    pytest.param(full_html_str, "About", id="test_extracts_all_links_with_href"),
    pytest.param(link_html_nohref_str, "yes", id="test_skips_links_without_href"),
    pytest.param(nested_html_str, "About", id="test_nested_with_links"),
]


@pytest.mark.parametrize("html, expected", LINKS_CASE)
def test_extract_links(html, expected):
    result = parse_html(html)
    assert result.links[0].text == expected
