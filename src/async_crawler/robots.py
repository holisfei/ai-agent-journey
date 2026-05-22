from urllib.parse import urlparse
import urllib.robotparser
from loguru import logger

def allow_fetch(url: str, user_agent: str = "*") -> bool:
    """
    检查 URL 是否被 robots.txt 允许抓取。
    失败时默认放行(robots.txt 缺失或解析失败不阻断爬虫)。
    """
    try:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        rp.read()

        allowed = rp.can_fetch(useragent=user_agent, url=url)
        if not allowed:
            logger.warning(f"robots.txt disallows: {url}")
        return allowed

    except Exception as e:
        logger.debug(f"robots.txt check failed for {url}: {e}")
        return True

