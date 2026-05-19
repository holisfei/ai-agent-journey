import pytest

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


@pytest.fixture(scope="module")
def full_html() -> str:
    """一个完整的、字段齐全的 HTML"""
    return full_html_str


minimal_html_str = """
    <html><body></body></html>
"""


@pytest.fixture(scope="module")
def minimal_html() -> str:
    """一个极简 HTML，几乎什么都没有"""
    return minimal_html_str


nested_html_str = """
    <html>
        <body>
            <div>
                <a href="/about">About</a>
            </div>
        </body>
    </html>
"""


@pytest.fixture(scope="module")
def nested_html() -> str:
    """一个嵌套的 HTML"""
    return nested_html_str
