from selectolax.parser import HTMLParser

from async_crawler.models import Link, PageContent

# ========= 解析入口  =========


def parse_html(html: str) -> PageContent:
    """从一个HTML网页解析所有内容"""
    tree = HTMLParser(html=html)
    return PageContent(
        title=_parse_title(tree=tree),
        description=_parse_description(tree=tree),
        headings=_parse_headings(tree=tree),
        links=_parse_links(tree=tree),
        text_length=_parse_length(tree=tree),
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
