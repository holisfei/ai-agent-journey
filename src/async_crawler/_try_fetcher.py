import asyncio

from async_crawler.fetcher import fetch_many


async def main():
    urls = [
        "https://www.baidu.com",
        "https://example.com",
        "https://httpbin.org/html",
        "https://httpbin.org/delay/1",  # 1 秒延时
        "https://httpbin.org/status/404",  # 404
        "https://this-domain-definitely-not-exist-xyz.com",  # DNS 失败
    ]
    results = await fetch_many(urls=urls)

    print(f"\n{'='*60}")
    print(f"完成 {len(results)} 个,统计:")

    from collections import Counter

    stats = Counter(r.status for r in results)
    for status, count in stats.items():
        print(f"  {status.value}: {count}")

    print("\n详细结果:")
    for r in results:
        print(f"【{r.status.value:>15}】 {r.url} ({r.elapsed_ms:.0f}ms)")
        if r.content and r.content.title:
            print(f"    title: {r.content.title}")


if __name__ == "__main__":
    asyncio.run(main())
