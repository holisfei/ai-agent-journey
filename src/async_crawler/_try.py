from async_crawler import parser

html = """
<html>
  <head>
    <title>Python Async Crawler Demo</title>
    <meta name="description" content="A demo page for learning Python">
  </head>
  <body>
    <h1>Welcome</h1>
    <h2>Section 1</h2>
    <h2>Section 2</h2>
    <p>Hello world, this is some body text.</p>
    <a href="/about">About</a>
    <a href="https://example.com">External</a>
    <a href="#section">Anchor</a>
    <a>No href here</a>
  </body>
</html>
"""

result = parser.parse_html(html=html)
print(result.model_dump_json(indent=2))  # indent格式化json
